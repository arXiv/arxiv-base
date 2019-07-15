# arxiv/fourohfour

ARG BASE_VERSION=latest

FROM arxiv/base:${BASE_VERSION}

RUN pipenv install arxiv-base arxiv-auth \
    && rm -rf ~/.cache/pip

EXPOSE 8000

WORKDIR /opt/arxiv

COPY wsgi.py uwsgi.ini /opt/arxiv/

LABEL version="0.15.9" \
  maintainer="arXiv <nextgen@arxiv.org>" \
  org.label-schema.schema-version="1.0" \
  org.label-schema.name="arXiv FourOhFour" \
  org.label-schema.description="Default error backend for arXiv k8s clusters" \
  org.label-schema.url="https://arxiv.github.io/arxiv-base" \
  org.label-schema.vcs-url="https://github.com/arxiv/arxiv-base" \
  org.label-schema.vendor="arXiv.org" \
  org.label-schema.version="0.15.9"

ENTRYPOINT ["pipenv", "run"]
CMD ["uwsgi", "--ini", "/opt/arxiv/uwsgi.ini"]
