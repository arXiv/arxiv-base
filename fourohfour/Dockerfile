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

ADD wsgi.py /opt/arxiv
ADD entrypoint.sh /opt/arxiv

ENTRYPOINT ["/opt/arxiv/entrypoint.sh"]
CMD ["--http-socket", ":8000", \
     "-M", \
     "-t 3000", \
     "--manage-script-name", \
     "--processes", "8", \
     "--threads", "1", \
     "--async", "100", \
     "--ugreen", \
     "--mount", "/=wsgi.py", \
     "--logformat", "%(addr) %(addr) - %(user_id)|%(session_id) [%(rtime)] [%(uagent)] \"%(method) %(uri) %(proto)\" %(status) %(size) %(micros) %(ttfb)"]
