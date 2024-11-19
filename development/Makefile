PROD_DB_PROXY_PORT := 2021
DEV_DB_PROXY_PORT := 6201

.PHONY: default hello proxy dev-proxy

default: hello

hello:
	echo "Hello"


proxy:
	/usr/local/bin/cloud-sql-proxy --address 0.0.0.0 --port ${PROD_DB_PROXY_PORT} arxiv-production:us-central1:arxiv-production-rep9 > /dev/null 2>&1 &

dev-proxy:
	/usr/local/bin/cloud-sql-proxy --address 0.0.0.0 --port ${DEV_DB_PROXY_PORT} arxiv-development:us-east4:arxiv-db-dev > /dev/null 2>&1 &

