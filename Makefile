PROD_DB_PROXY_PORT := 2021


.PHONY: db-models prod-proxy test

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


prod-proxy:
	/usr/local/bin/cloud-sql-proxy --address 0.0.0.0 --port ${PROD_DB_PROXY_PORT} arxiv-production:us-central1:arxiv-production-rep9 > /dev/null 2>&1 &

test: venv/bin/poetry
	venv/bin/poetry run pytest --cov=arxiv.base fourohfour --cov-fail-under=67 arxiv/base fourohfour
	TEST_ARXIV_DB_URI=mysql://testuser:testpassword@127.0.0.1:13306/testdb venv/bin/poetry run pytest --cov=arxiv --cov-fail-under=25 arxiv
	TEST_ARXIV_DB_URI=mysql://testuser:testpassword@127.0.0.1:13306/testdb venv/bin/poetry run python tests/run_app_tests.py
