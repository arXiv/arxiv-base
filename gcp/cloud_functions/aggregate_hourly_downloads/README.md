# summary
aggregates hourly download stats into a table grouping by category, country and download type. In response to a pubsub takes data from arxiv_stats.papers_downloaded_by_ip_recently. Looks up the categories for each paper from our main database and aggregates the data. Then writes this to another table which is configured by the WRITE_TABLE enviroment variable

# commands
this will need to be in its own dev enviroment seperate from base where you can install the dependencies. This way the function doesn't get surprised by changes made to the rest of base that it isnt ready for.

to install 
` pip install -r src/requirements.txt `
and 
` pip install -r src/requirements-dev.txt `

# enviroment variables for running locally
```
export ENVIRONMENT=DEVELOPMENT LOG_LEVEL=INFO  WRITE_TABLE='sqlite:///../tests/output_test.db' LOG_LOCALLY=1

```

you need everything in the env file plus:

```
export CLASSIC_DB_URI='SECRET_HERE'

```
the classic db URI always needs to be for the prodution database to get category data for recent papers, adn you will need to set up a connection to the database

# to run the manual backfill

enviroment variables:
```
export LOG_LOCALLY=1
export CLASSIC_DB_URI='SECRET_HERE'
export WRITE_TABLE='SECRET_HERE'
```
the classic DB URI should be for the main production database and the write table is currently the latexml db 
secrets can be found in GCP and a connection to the databases will need to be established with something like cloud_sql_proxy

run like:
```
python main.py 2024-10-03-00 2024-10-05-23
```
this will run for all data for october 3rd through 5th inclusive, hours can be specified with the last two numbers
at roughly 45 seconds per hour block running an entire month can take 9 hours


# to run the cloud function

to run use this in the src folder
` functions-framework --target=aggregate_hourly_downloads --signature-type=cloudevent `

message data options:
the function looks for a message like {"state": "SUCCEEDED"} to trigger

to trigger run a curl command with a cloud event, heres an example you can use: 
note that the data is base 64 encoded, and that return values from cloud functions seem to be useless
 ```
 curl localhost:8080 \
  -X POST \
  -H "Content-Type: application/json" \
  -H "ce-id: 123451234512345" \
  -H "ce-specversion: 1.0" \
  -H "ce-time: 2020-01-02T12:34:56.789Z" \
  -H "ce-type: google.cloud.pubsub.topic.v1.messagePublished" \
  -H "ce-source: //pubsub.googleapis.com/projects/MY-PROJECT/topics/MY-TOPIC" \
  -d '{
        "message": {
          "data": "eyJzdGF0ZSI6ICJTVUNDRUVERUQifQ==",
          "attributes": {
             "attr1":"attr1-value"
          }
        },
        "subscription": "projects/MY-PROJECT/subscriptions/MY-SUB"
      }'
    
 ```

to run tests 
` pytest tests `