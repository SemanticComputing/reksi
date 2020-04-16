FROM alpine:3.8

ENV GUNICORN_WORKER_AMOUNT 4
ENV GUNICORN_RELOAD ""

RUN apk add python3-dev gcc libc-dev && rm -rf /var/cache/apk/*

COPY requirements.txt ./requirements.txt
RUN pip3 install -r requirements.txt

RUN pip3 install gunicorn

RUN python3 -c "import nltk; nltk.download('punkt', '/usr/share/nltk_data')"

WORKDIR /app

COPY src ./

RUN mkdir src

COPY conf ./conf

RUN sed -i "s/from src.DateConverter import \*/from DateConverter import \*/" /app/RegEx.py

COPY language-resources ./language-resources

RUN chgrp -R 0 /app \
    && chmod -R g+rwX /app

EXPOSE 5000

USER 9008

COPY run /run.sh

ENTRYPOINT [ "/run.sh" ]