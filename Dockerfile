FROM python:3.6-slim-buster

COPY requirements.txt ./requirements.txt
RUN pip3 install -r requirements.txt
RUN pip3 install gunicorn
ENV GUNICORN_BIN /usr/local/bin/gunicorn

RUN python3 -c "import nltk; nltk.download('punkt', '/usr/share/nltk_data')"

WORKDIR /app

COPY language-resources ./language-resources

COPY src ./

ENV CONF_FILE /app/conf/app_config.ini
COPY conf/app_config.ini $CONF_FILE

ENV LOG_CONF_FILE=/app/conf/logging.ini
COPY conf/logging.ini $LOG_CONF_FILE
RUN sed -i s/logging\.handlers\.RotatingFileHandler/logging\.StreamHandler/ $LOG_CONF_FILE \
 && sed -i s/logging\.FileHandler/logging\.StreamHandler/ $LOG_CONF_FILE \
 && sed -E -i s/^args=.+$/args=\(sys.stdout,\)/ $LOG_CONF_FILE

RUN sed -i "s/from src.DateConverter import \*/from DateConverter import \*/" /app/RegEx.py
RUN chgrp -R 0 /app \
    && chmod -R g+rwX /app

ENV GUNICORN_WORKER_AMOUNT 4
ENV GUNICORN_RELOAD ""

EXPOSE 5000

USER 9008

COPY run /run.sh

ENTRYPOINT [ "/run.sh" ]