# Fastly log ingest
This is a small python program that listens to a GCP pub/sub for fastly log messages and writes those to 
the GCP logging API. Then they can be viewed with tools like log exporter or used in log based metrics.

## Rational
Fastly does not have a log tool. They integrate with several platforms and expect user to 
choose a tool like Elasticsearch. 
For information see [fastly's log docs](https://www.fastly.com/documentation/guides/integrations/logging/)

Fastly does not have a direct log integration with GCP logging API. They do have integration 
with GCP Big query.

Why is this not a cloud function or cloud run? We often want to do as much as possible 
serverless to avoid managing VMs. Yet this is written as a program than runs on a VM. Why?
1. There is limit to the number of logging API calls per minute. At times arxiv.org 
   has seen very high rates of traffic. If each log line was sent as a single API call 
   we could reach those limits during times of excessive traffic.
2. In light of 1. we can use GCP logging API batch feature to reduce our number of calls
   by a factor of 100
3. Cloud run and cloud functions do not immediately support batching since ACK the message
   at completion. This app will receive pubsub messages batch them up and only send an ACK once
   the batch has been sent to GCP logging. 

## Deploy
For deploy see [Dockerfile](/deploy/Dockerfile-fastlylogingest) 

## Development
To develop locally setup up local GCP credentials with privileges similar to what is in
the deployment guide Docker file. Run the program like this:
    
    cd arxiv-base
    python -m venv venv
    venv/bin/activate
    poetry install
    VERBOSE=1 SHOW_PER_THREAD_RATES=1 python arxiv/ops/fastly_log_ingest/app.py