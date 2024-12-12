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

Since this is reading from pub/sub, it is safe to stop and restart the service. Any messages sent while down will be kept in the pub/sub subscription queue.
The service will gracefully shutdown on VM stop, to SIGTERM and to SIGNINT.

## Deploy
This runs as a managed instance group `fastly-log-ingest-arxiv-org-timebound-mig`. We created this group by making a 
docker image, setting up a VM running that image, then converting it to a MIG.

To deploy, make a docker image, push to GCP, then make a GCP VM with docker OS
and the image.  Here is the  [Dockerfile](/deploy/Dockerfile-fastlylogingest)

    gcloud auth configure-docker us-central1-docker.pkg.dev # one time setup
    docker build -f deploy/Dockerfile-fastlylogingest -t arxiv-fastly-log-ingest .
    TAG=us-central1-docker.pkg.dev/arxiv-production/arxiv-docker/arxiv-fastly-log-ingest
    docker tag arxiv-fastly-log-ingest $TAG
    docker push $TAG


It will need to be run with a SA that can read from the pub/sub subscription and write to the project logs.
Make a service account `fastly-logs-ingest`. Grant it Pub/Sub subscriber, logging writer, Artifact Registry reader on us-central1-docker.pkg.dev/arxiv-production/arxiv-docker

Then:
- create a e2-small VM with a that docker image with
- service account `fastly-logs-ingest`
- access scopes set to "allow full access to all cloud apis"
- set it to run a container
  - us-central1-docker.pkg.dev/arxiv-production/arxiv-docker/arxiv-fastly-log-ingest
  - set  Allocate a pseudo-TTY true
  - no env vars, mount points or args are needed
- set GCP logging to on
- under provisioning advanced config:
  - click set time limit
  - max duration to 8 hours
  - delete on termination
- Set label `fastly: fastly-log-ingest`
- under advanced
  - under management
    - check "Enable Logging" to allow container logs to go to log explorer


An `e2-small` VM can handle over 1k messages/sec.

Check the logs of the VM to see if there are the expected rate messages.

To update, make a new docker image, push to GCP and restart the MIG VMs. They should pick up the newest image on start.


## Development
To develop locally setup up local GCP credentials with privileges similar to what is in
the deployment guide Docker file. Run the program like this:

    cd arxiv-base
    python -m venv venv
    venv/bin/activate
    poetry install
    VERBOSE=1 SHOW_PER_THREAD_RATES=1 python arxiv/ops/fastly_log_ingest/app.py
## Notes
Logging full stack traces drives up CPU use.
