# summary
aggregates hourly download stats into a table grouping by category, country and download type. In response to a pubsub takes data from arxiv_stats.papers_downloaded_by_ip_recently. Looks up the categories for each paper from our main database and aggregates the data. Then writes this to another table which is configured by the WRITE_TABLE enviroment variable

# commands
this will need to be in its own dev enviroment seperate from base where you can install the dependencies. This way the function doesn't get surprised by changes made to the rest of base that it isnt ready for.

to install 
` pip install -r src/requirements.txt `
and 
` pip install -r src/requirements-dev.txt `

# enviroment variables
```
export ENVIRONMENT=DEVELOPMENT LOG_LEVEL=INFO DOWNLOAD_TABLE=arxiv-development.arxiv_stats.papers_downloaded_by_ip_recently WRITE_TABLE='sqlite:///../tests/output_test.db'

```

you need everything in the env file plus:

```
export CLASSIC_DB_URI='SECRET_HERE'
export WRITE_TABLE='SECRET_HERE'
```
the classic db URI always needs to be for the prodution database to get category data for recent papers

to run use this in the src folder
` functions-framework --target=aggregate_hourly_downloads --signature-type=cloudevent `

message data options:
currently the contents of the message don't matter any message triggers the run

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
          "data": "eyJwYXBlcl9pZCI6IjEwMDguMzIyMiIsICJvbGRfY2F0ZWdvcmllcyI6ImVlc3MuU1kgaGVwLWxhdCJ9",
          "attributes": {
             "attr1":"attr1-value"
          }
        },
        "subscription": "projects/MY-PROJECT/subscriptions/MY-SUB"
      }'
    
 ```

to run tests 
` pytest tests `