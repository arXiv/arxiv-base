import json
import base64
import os
from typing import Set, Dict, List, Literal, Tuple, Any
from datetime import datetime

from arxiv.taxonomy.category import Category
from arxiv.taxonomy.definitions import CATEGORIES
from arxiv.db import Session
from arxiv.db.models import Metadata, DocumentCategory
from arxiv.identifier import Identifier

import functions_framework
from cloudevents.http import CloudEvent

from google.cloud import bigquery
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Enum, PrimaryKeyConstraint, Row, tuple_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, aliased

MAX_QUERY_TO_WRITE=1000 #the latexmldb we write to has a stack size limit

#logging setup
if not(os.environ.get('LOG_LOCALLY')):
    import google.cloud.logging
    client = google.cloud.logging.Client()
    client.setup_logging()
import logging 
log_level_str = os.getenv('LOG_LEVEL', 'INFO')
log_level = getattr(logging, log_level_str.upper(), logging.INFO)
logging.basicConfig(level=log_level)

# Initialize BigQuery client
bq_client = bigquery.Client()

DownloadType = Literal["pdf", "html", "src"]

class PaperCategories:
    paper_id: str
    primary : Category
    crosses: Set[Category]

    def __init__(self, id:str):
        self.paper_id=id
        self.primary=None
        self.crosses=set()

    def add_primary(self,cat:str):
        if self.primary != None: #this function should only get called once per paper
            logging.error(f"Multiple primary categories for {self.paper_id}: {self.primary} and {cat}")
            self.add_cross(cat) #add as a cross just to keep data
        else:
            catgory=CATEGORIES[cat]
            canon=catgory.get_canonical()
            self.primary=canon
            self.crosses.discard(canon) #removes from crosses if present, the same category cant be both primary and cross. This is relevant because an alternate name may be listed as a cross list

    def add_cross(self, cat:str):
        catgory=CATEGORIES[cat]
        canon=catgory.get_canonical()
        #avoid dupliciates of categories with other names
        if self.primary is None or canon != self.primary:
            self.crosses.add(canon)

    def __eq__(self, other):
        if not isinstance(other, PaperCategories):
            return False
        return (self.paper_id == other.paper_id and
                self.primary == other.primary and
                self.crosses == other.crosses)

    def __repr__(self):
        crosses_str = ', '.join(cat.id for cat in self.crosses)
        return f"Paper: {self.paper_id} Primary: {self.primary.id} Crosses: {crosses_str}"

class DownloadData:
    def __init__(self, paper_id: str, country: str, download_type: DownloadType, time: datetime, num: int):
        self.paper_id = paper_id
        self.country = country
        self.download_type = download_type
        self.time = time
        self.num = num

    def __repr__(self) -> str:
        return (f"DownloadData(paper_id='{self.paper_id}', country='{self.country}', "
                f"download_type='{self.download_type}', time='{self.time}', "
                f"num={self.num})")

class DownloadCounts:
    def __init__(self, primary: int =0, cross: int=0):
        self.primary=primary
        self.cross=cross

    def __eq__(self, other):
        if isinstance(other, DownloadCounts):
            return self.primary==other.primary and self.cross==other.cross
        else:
            return False
    def __repr__(self):
        return f"Count(primary: {self.primary}, cross: {self.cross})"

class DownloadKey:
    def __init__(self, time: datetime, country: str, download_type: DownloadType, archive: str, category_id: str):
        self.time = time  
        self.country = country
        self.download_type = download_type
        self.archive=archive
        self.category=category_id

    def __eq__(self, other):
        if isinstance(other, DownloadKey):
            return (self.country == other.country and 
                    self.download_type == other.download_type and
                    self.category == other.category
                    and self.time.date() == other.time.date()
                    and self.time.hour == other.time.hour
                    )
        return False

    def __hash__(self):
        return hash((self.time.date(), self.time.hour, self.country, self.download_type, self.category))

    def __repr__(self):
        return f"Key(type: {self.download_type}, cat: {self.category}, country: {self.country}, day: {self.time.day} hour: {self.time.hour})"

@functions_framework.cloud_event
def aggregate_hourly_downloads(cloud_event: CloudEvent):
    """ get downloads data and aggregate but category country and download type
    """

    data=json.loads(base64.b64decode(cloud_event.get_data()['message']['data']).decode())
    state= data.get("state","")
    if state!="SUCCEEDED":
        logging.debug(f"ignored message: {data}")
        return

    #get and check enviroment data
    enviro=os.environ.get('ENVIRONMENT')
    download_table=os.environ.get('DOWNLOAD_TABLE')
    write_table=os.environ.get('WRITE_TABLE')
    if any(v is None for v in (enviro, download_table, write_table)):
        logging.critical(f"Missing enviroment variable(s): ENVIRONMENT:{enviro}, DOWNLOAD_TABLE: {download_table}, WRITE_TABLE: {write_table}")
        return #dont bother retrying
    elif enviro == "PRODUCTION":
        if "development" in download_table or "development" in write_table: 
            logging.warning(f"Referencing development project in production! Downloads {download_table} Write {write_table}")
    elif enviro == "DEVELOPMENT":
        if "production" in download_table or "production" in write_table: 
            logging.warning(f"Referencing production project in development! Downloads {download_table} Write {write_table}")
    else:
        logging.error(f"Unknown Enviroment: {enviro}")
        return #dont bother retrying

    #get the download data
    query = f"""
        SELECT 
            paper_id, 
            geo_country, 
            download_type, 
            start_dttm, 
            num_downloads 
        FROM {download_table} 
        
    """
    query_job = bq_client.query(query)
    download_result = query_job.result() 

    #process and store returned data
    paper_ids=set() #only look things up for each paper once
    download_data: List[DownloadData]=[] #not a dictionary because no unique keys
    problem_rows: List[Tuple[Any], Exception]=[]
    problem_row_count=0
    for row in download_result:
        try:
            d_type = "src" if row['download_type'] == "e-print" else row['download_type'] #combine e-print and src downloads
            paper_id=Identifier(row['paper_id']).id
            download_data.append(
                DownloadData(
                    paper_id=paper_id,
                    country=row['geo_country'],
                    download_type=d_type,
                    time=row['start_dttm'].replace(minute=0, second=0, microsecond=0), #bucketing by hour
                    num=row['num_downloads']
                )
            )
            paper_ids.add(paper_id)
        except Exception as e:
            problem_row_count+=1
            problem_rows.append((tuple(row), e)) if len(problem_rows) < 20 else None
            continue #dont count this download
    if problem_row_count>0:
        logging.warning(f"Problem processing {problem_row_count} rows")
        logging.debug(f"Selection of problem row errors: {problem_rows}")

    logging.info(f"fetched {len(download_data)} rows, unique paper ids: {len(paper_ids)}")

    if len(paper_ids) ==0:
        logging.critical("No data retrieved from BigQuery")
        return #this will prevent retries (is that good?)
    
    #find categories for all the papers
    paper_categories=get_paper_categories(paper_ids)
    if len(paper_categories) ==0:
        logging.critical("No category data retrieved from database")
        return #this will prevent retries (is that good?)

    #aggregate download data
    aggregated_data=aggregate_data(download_data, paper_categories)
    
    #write all_data to tables  
    insert_into_database(aggregated_data, write_table)


def get_paper_categories(paper_ids: Set[str])-> Dict[str, PaperCategories]:
    #get the category data for papers
    meta=aliased(Metadata)
    dc=aliased(DocumentCategory)    
    paper_cats = (
        Session.query(meta.paper_id, dc.category, dc.is_primary)
        .join(meta, dc.document_id == meta.document_id)
        .filter(meta.paper_id.in_(paper_ids)) 
        .filter(meta.is_current==1)
        .all()
    )

    return process_paper_categories(paper_cats)

def process_paper_categories(data: List[Row[Tuple[str, str, int]]])-> Dict[str, PaperCategories]:
    #format paper categories into dictionary
    paper_categories: Dict[str, PaperCategories]={}
    for row in data:
        paper_id, cat, is_primary = row
        entry=paper_categories.setdefault(paper_id, PaperCategories(paper_id))
        if is_primary ==1:
            entry.add_primary(cat)
        else:
            entry.add_cross(cat)

    return paper_categories

def aggregate_data(download_data: List[DownloadData], paper_categories: Dict[str, PaperCategories]) -> Dict[DownloadKey, DownloadCounts]:
    """creates a dictionary of download counts by time, country, download type, and category
        goes through each download entry, matches it with its caegories and adds the number of downloads to the count
    """
    all_data: Dict[DownloadKey, DownloadCounts]={}
    missing_data: List[str]=[]
    missing_data_count=0
    for entry in download_data:
        try:
            cats=paper_categories[entry.paper_id]
        except KeyError as e:
            missing_data_count+=1
            missing_data.append(entry.paper_id) if len(missing_data) < 20 else None #dont make the list too long
            continue #dont process this paper

        #record primary
        key=DownloadKey(entry.time, entry.country, entry.download_type, cats.primary.in_archive, cats.primary.id)
        value=all_data.get(key, DownloadCounts())
        value.primary+=entry.num
        all_data[key]=value
        
        #record for each cross
        for cat in cats.crosses:
            key=DownloadKey(entry.time, entry.country, entry.download_type, cat.in_archive, cat.id)
            value=all_data.get(key, DownloadCounts())
            value.cross+=entry.num
            all_data[key]=value

    if missing_data_count>0:
        logging.warning(f"Could not find category data for {missing_data_count} paper_ids (may be invalid)")
        logging.debug(f"Example paper_ids with no category data: {missing_data}")

    return all_data

def insert_into_database(aggregated_data: Dict[DownloadKey, DownloadCounts], db_uri: str):
    """adds the data from an hour of downloads into the database
        uses bulk insert and update statements to increase efficiency
        first compiles all the keys for the data we would like to add and checks for their presence in the database
        present items are added to run update for, and removed from the aggregated dictionary
        remaining items are inserted
        data with duplicate keys will be overwritten to allow for reruns with updates
    """
    #set up table
    Base = declarative_base()
    class HourlyDownloadData(Base):
        __tablename__ = 'hourly_download_data'     
        country = Column(String(255), primary_key=True)
        download_type = Column(String(16), Enum('pdf', 'html', 'src', name='download_type_enum'), primary_key=True)
        archive = Column(String(16))
        category = Column(String(32), primary_key=True)
        primary_count = Column(Integer)
        cross_count = Column(Integer)
        start_dttm = Column(DateTime, primary_key=True)
        __table_args__ = (
            PrimaryKeyConstraint('country', 'download_type', 'category', 'start_dttm'),
        )

    # Setup database connection
    engine = create_engine(db_uri)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    #see what data is already there
    keys_to_check = [
        (item.country, item.download_type, item.category, item.time)
        for item in aggregated_data.keys()
    ]
    all_keys_to_update=[]
    for i in range(0, len(keys_to_check), MAX_QUERY_TO_WRITE):
        #query a section of data
        existing_records = session.query(HourlyDownloadData).filter(
            tuple_(
                HourlyDownloadData.country,
                HourlyDownloadData.download_type,
                HourlyDownloadData.category,
                HourlyDownloadData.start_dttm
            ).in_(keys_to_check[i:i+MAX_QUERY_TO_WRITE])
        ).all()

        #record found records
        keys_to_update=[
            DownloadKey(
                time=record.start_dttm,
                country=record.country,
                download_type=record.download_type,
                archive=record.archive,
                category_id=record.category
            )
            for record in existing_records
        ]
        all_keys_to_update += keys_to_update

    #create data to be updated vs inserted
    update_data=[]
    for key in all_keys_to_update:
        counts=aggregated_data[key]
        entry={
            'country': key.country,
            'download_type': key.download_type,
            'archive': key.archive,
            'category': key.category,
            'start_dttm': key.time,
            'primary_count': counts.primary,
            'cross_count': counts.cross
        }
        update_data.append(entry)
        del aggregated_data[key] #remove before insert

    #all the new data to insert
    data_to_insert = [
        HourlyDownloadData(
            country=key.country,
            download_type=key.download_type,
            archive=key.archive,
            category=key.category,
            primary_count=counts.primary,
            cross_count=counts.cross,
            start_dttm=key.time
        )
        for key, counts in aggregated_data.items()
    ]

    #add data
    for i in range(0, len(data_to_insert), MAX_QUERY_TO_WRITE):
        session.bulk_save_objects(data_to_insert[i:i+MAX_QUERY_TO_WRITE])
    #update existing data
    for i in range(0, len(update_data), MAX_QUERY_TO_WRITE):
        session.bulk_update_mappings(HourlyDownloadData, update_data[i:i+MAX_QUERY_TO_WRITE])
    session.commit()
    session.close()
    logging.info(f"added {len(data_to_insert)} rows, updated {len(update_data)} rows")
    return
