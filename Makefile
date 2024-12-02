PROD_DB_PROXY_PORT := 2021


.PHONY: db-models prod-proxy

default: venv/bin/poetry

venv/bin/poetry: venv/bin/pip
	. venv/bin/activate && pip install poetry

venv/bin/pip: venv
	. venv/bin/activate && pip install --upgrade pip

venv:
	python3.11 -m venv venv

~/.arxiv:
	mkdir ~/.arxiv

 ~/.arxiv/arxiv-db-prod-readonly:  ~/.arxiv
	op item get as76tjqjnr5wduypygusvfyy34 --fields username,password --reveal | python3 -c "import sys;import urllib.parse; unpw=sys.stdin.read().split(','); sys.stdout.write('mysql://%s:%s@127.0.0.1:2021/arXiv' % (unpw[0].strip(),urllib.parse.quote(unpw[1].strip(),safe='*')))" > $@

db-models: arxiv/db/autogen_models.py

arxiv/db/autogen_models.py: arxiv/db/autogen_models_patch.diff ~/.arxiv/arxiv-db-prod-readonly
	@PROD_ARXIV_DB_URI=`cat ~/.arxiv/arxiv-db-prod-readonly`; . venv/bin/activate && \
	poetry run sqlacodegen "$$PROD_ARXIV_DB_URI" --outfile arxiv/db/autogen_models.py && \
	poetry run python3 development/patch_db_models.py arxiv/db/autogen_models.py arxiv/db/arxiv_db_metadata.json
	patch arxiv/db/autogen_models.py arxiv/db/autogen_models_patch.diff

arxiv/db/autogen_models_patch.diff:
	@PROD_ARXIV_DB_URI=`cat ~/.arxiv/arxiv-db-prod-readonly`; . venv/bin/activate && \
	poetry run sqlacodegen "$$PROD_ARXIV_DB_URI" --outfile arxiv/db/.autogen_models.py
	diff -c arxiv/db/.autogen_models.py arxiv/db/autogen_models.py > arxiv/db/autogen_models_patch.diff

prod-proxy:
	/usr/local/bin/cloud-sql-proxy --address 0.0.0.0 --port ${PROD_DB_PROXY_PORT} arxiv-production:us-central1:arxiv-production-rep9 > /dev/null 2>&1 &
