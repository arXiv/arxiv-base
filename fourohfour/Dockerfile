# arxiv/fourohfour

ARG BASE_VERSION=latest

FROM arxiv/base:${BASE_VERSION}

LABEL org.label-schema.name="arXiv FourOhFour" \
  org.label-schema.description="Default error backend for arXiv k8s clusters"

WORKDIR /opt/arxiv

RUN pipenv install arxiv-base arxiv-auth \
    && rm -rf ~/.cache/pip

EXPOSE 8000

COPY wsgi.py uwsgi.ini /opt/arxiv/

LABEL org.label-schema.version="0.15.9"

ENTRYPOINT ["pipenv", "run"]
CMD ["uwsgi", "--ini", "/opt/arxiv/uwsgi.ini"]
