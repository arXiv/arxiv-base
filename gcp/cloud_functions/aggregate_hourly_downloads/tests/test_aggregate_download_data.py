from datetime import datetime
from arxiv.taxonomy.definitions import CATEGORIES

import sys, os
sys.path.append( os.path.join(os.path.dirname(__file__), "..", "src") )
from main import process_paper_categories, PaperCategories, DownloadData, DownloadKey, DownloadCounts, aggregate_data

def test_process_cats_basic():
    "tests basic processing for "
    data=[
        ("1234.5678", "math.GM", 1),
        ("1234.5679", "hep-lat", 1),
        ("1234.5679", "q-fin.CP", 0),
        ("1234.5679", "q-fin.PM", 0)
    ]
    result= process_paper_categories(data)

    expected1=PaperCategories("1234.5678")
    expected1.add_primary("math.GM")
    expected2=PaperCategories("1234.5679")
    expected2.add_primary("hep-lat")
    expected2.add_cross("q-fin.CP")
    expected2.add_cross("q-fin.PM")
    expected={
        "1234.5678":expected1,
        "1234.5679":expected2,
    }
    assert result == expected

def test_paper_categories_basic():
    "tests that paper categories class works as expected"

    #initial creation
    item= PaperCategories("1234.5678")
    assert item.paper_id == "1234.5678"
    assert item.primary is None
    assert item.crosses == set()

    #add a crosslist
    item.add_cross("hep-lat")
    assert item.paper_id == "1234.5678"
    assert item.primary is None
    assert item.crosses == {CATEGORIES["hep-lat"]}

    #add a primary listing
    item.add_primary("physics.ins-det")
    assert item.paper_id == "1234.5678"
    assert item.primary == CATEGORIES["physics.ins-det"]
    assert item.crosses == {CATEGORIES["hep-lat"]}

    #add another crosslist
    item.add_cross("q-bio.PE")
    assert item.paper_id == "1234.5678"
    assert item.primary == CATEGORIES["physics.ins-det"]
    assert item.crosses == {CATEGORIES["hep-lat"], CATEGORIES["q-bio.PE"]}

def test_paper_categories_subsumed():
    """test that only the canonical version of subsumed archives is used 
    duplicates caused by this are avoided"""

    #converts to canon correctly
    item= PaperCategories("1234.5678")
    item.add_cross("chao-dyn")
    assert item.paper_id == "1234.5678"
    assert item.primary is None
    assert item.crosses == {CATEGORIES["nlin.CD"]}

    #doesnt duplicate cross
    item.add_cross("chao-dyn")
    assert item.primary is None
    assert item.crosses == {CATEGORIES["nlin.CD"]}

    #doesn't duplicate even if alt name is used
    item.add_cross("nlin.CD")
    assert item.primary is None
    assert item.crosses == {CATEGORIES["nlin.CD"]}

    #adding as primary uses canonical name and removes duplicate entry in cross
    item.add_primary("chao-dyn")
    assert item.primary == CATEGORIES["nlin.CD"]
    assert item.crosses == set()

    #cant add a matching crosslist
    item.add_cross("nlin.CD")
    assert item.primary == CATEGORIES["nlin.CD"]
    assert item.crosses == set()

    #can add alternately named crosslist
    item.add_cross("chao-dyn")
    assert item.primary == CATEGORIES["nlin.CD"]
    assert item.crosses == set()

def test_paper_categories_alias():
    """test that only the canonical version of alias is used 
    duplicates caused by this are avoided"""

    #converts to canon correctly
    item= PaperCategories("1234.5678")
    item.add_cross("cs.SY")
    assert item.paper_id == "1234.5678"
    assert item.primary is None
    assert item.crosses == {CATEGORIES["eess.SY"]}

    #doesnt duplicate cross
    item.add_cross("cs.SY")
    assert item.primary is None
    assert item.crosses == {CATEGORIES["eess.SY"]}

    #doesn't duplicate even if alt name is used
    item.add_cross("eess.SY")
    assert item.primary is None
    assert item.crosses == {CATEGORIES["eess.SY"]}

    #adding as primary uses canonical name and removes duplicate entry in cross
    item.add_primary("cs.SY")
    assert item.primary == CATEGORIES["eess.SY"]
    assert item.crosses == set()

    #cant add a matching crosslist
    item.add_cross("eess.SY")
    assert item.primary == CATEGORIES["eess.SY"]
    assert item.crosses == set()

    #can add alternately named crosslist
    item.add_cross("cs.SY")
    assert item.primary == CATEGORIES["eess.SY"]
    assert item.crosses == set()

def test_aggregate_data():
    paper1=PaperCategories("1234.5678")
    paper1.add_primary("math.GM")
    paper1.add_cross("q-fin.CP")
    paper1.add_cross("q-fin.PM")

    paper2=PaperCategories("1234.5679")
    paper2.add_primary("hep-lat")

    paper3=PaperCategories("1234.5680")
    paper3.add_primary("hep-lat")
    paper3.add_cross("q-fin.CP")
    paper3.add_cross("math.GM")
    paper_categories = {
        "1234.5678": paper1,
        "1234.5679": paper2,
        "1234.5680": paper3
    }

    hour=datetime(2024, 7, 26, 13, 0) 

    download_data = [
        DownloadData("1234.5678", "USA", "pdf", hour, 10),
        DownloadData("1234.5678", "Ireland", "pdf", hour, 5),
        DownloadData("1234.5679", "Ireland", "pdf", hour, 3),
        DownloadData("1234.5680", "Ireland", "pdf", hour, 1)
    ]

    #from first entry
    key1=DownloadKey(hour, "USA", "pdf", "math", "math.GM")
    key2=DownloadKey(hour, "USA", "pdf", "q-fin", "q-fin.CP")
    key3=DownloadKey(hour, "USA", "pdf", "q-fin", "q-fin.PM")
    #from second entry
    key4=DownloadKey(hour, "Ireland", "pdf", "math", "math.GM")
    key5=DownloadKey(hour, "Ireland", "pdf", "q-fin", "q-fin.CP")
    key6=DownloadKey(hour, "Ireland", "pdf", "q-fin", "q-fin.PM")
    #from 3rd entry
    key7=DownloadKey(hour, "Ireland", "pdf", "hep-lat", "hep-lat")
    #4th entry uses existing keys
    expected = {
        key1: DownloadCounts(10,0),
        key2: DownloadCounts(0,10),
        key3: DownloadCounts(0,10),
        key4: DownloadCounts(5,1),
        key5: DownloadCounts(0,6),
        key6: DownloadCounts(0,5),
        key7: DownloadCounts(4,0),
    }
   
    result = aggregate_data(download_data, paper_categories)

    #test one by one for debugging
    assert key1 in result.keys()
    assert result[key1]==DownloadCounts(10,0)
    assert key2 in result.keys()
    assert result[key2]==DownloadCounts(0,10)
    assert key3 in result.keys()
    assert result[key3]==DownloadCounts(0,10)
    assert key4 in result.keys()
    assert result[key4]==DownloadCounts(5,1)
    assert key5 in result.keys()
    assert result[key5]==DownloadCounts(0,6)
    assert key6 in result.keys()
    assert result[key6]==DownloadCounts(0,5)
    assert key7 in result.keys()
    assert result[key7]==DownloadCounts(4,0)

    assert result == expected