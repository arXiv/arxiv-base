# arxiv/fourohfour

FROM arxiv/base:0.14.2

WORKDIR /opt/arxiv

RUN yum install -y which mysql mysql-devel

ENV LOGLEVEL 10
ENV LC_ALL en_US.utf-8
ENV LANG en_US.utf-8

RUN pip install -U pip pipenv uwsgi
RUN pipenv install arxiv-base arxiv-auth

EXPOSE 8000

ADD wsgi.py uwsgi.ini entrypoint.sh /opt/arxiv/

ENTRYPOINT ["pipenv", "run"]
CMD ["uwsgi", "--ini", "/opt/arxiv/uwsgi.ini"]
