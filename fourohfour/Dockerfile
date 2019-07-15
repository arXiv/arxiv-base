# arxiv/fourohfour

ARG BASE_VERSION=latest

FROM arxiv/base:${BASE_VERSION}

LABEL org.opencontainers.image.title="arXiv FourOhFour" \
  org.opencontainers.image.description="Default error backend for arXiv k8s clusters"

WORKDIR /opt/arxiv

LABEL org.label-schema.version="0.15.9"

RUN pipenv install arxiv-base arxiv-auth \
    && rm -rf ~/.cache/pip

EXPOSE 8000

COPY wsgi.py uwsgi.ini /opt/arxiv/

ENTRYPOINT ["pipenv", "run"]
CMD ["uwsgi", "--ini", "/opt/arxiv/uwsgi.ini"]
