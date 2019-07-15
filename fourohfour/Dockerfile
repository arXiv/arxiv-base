# arxiv/fourohfour

FROM arxiv/base:ARXIVNG-2462

RUN pipenv install arxiv-base arxiv-auth \
    && rm -rf ~/.cache/pip

EXPOSE 8000

COPY wsgi.py uwsgi.ini /opt/arxiv/

ENTRYPOINT ["pipenv", "run"]
CMD ["uwsgi", "--ini", "/opt/arxiv/uwsgi.ini"]
