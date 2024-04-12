FROM mysql:8.0.36-debian

######## Install Python 3.11 ########

RUN apt install software-properties-common -y
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update -y
RUN apt install python3.11 python3-pip -y

###### Install Cloud SQL Proxy ######

WORKDIR /cloudsql

RUN apt-get install -y curl

RUN curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.10.1/cloud-sql-proxy.linux.amd64
RUN chmod +x cloud-sql-proxy
