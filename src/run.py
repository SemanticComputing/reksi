from flask import Flask, jsonify
from flask import request
import argparse
import sys, os
import logging, json
import re
import time
import datetime
import nltk
import nltk.data
import xml.dom.minidom
import xml.etree.ElementTree as ET
from RegEx import ExecuteRegEx
from datetime import datetime as dt
import csv
import logging, logging.config

app = Flask(__name__)

logging.config.fileConfig(fname='conf/logging.ini', disable_existing_loggers=False)
logger = logging.getLogger('run')

@app.before_request
def before_request():
    if True:
        logger.info("HEADERS: %s", request.headers)
        logger.info("REQ_path: %s", request.path)
        logger.info("ARGS: %s",request.args)
        logger.info("DATA: %s",request.data)
        logger.info("FORM: %s",request.form)

def parse_input(request):
    input = None
    if request.method == 'GET':
        text = request.args.get('text')
        sentences = tokenization(text)
        input = {i: sentences[i] for i in range(0, len(sentences))}
    else:
        if request.headers['Content-Type'] == 'text/plain':
            sentences = tokenization(str(request.data.decode('utf-8')))
            input = {i:sentences[i] for i in range(0, len(sentences))}
        else:
            logger.warning("Bad type", request.headers['Content-Type'])
    return input

def setup_tokenizer():
    tokenizer = nltk.data.load('tokenizers/punkt/finnish.pickle')
    with open('language-resources/abbreviations.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=';')
        for row in csv_reader:
            tokenizer._params.abbrev_types.add(row[0])
    for i in range(1, 301):
        tokenizer._params.abbrev_types.add(str(i))
    return tokenizer

def tokenization(text):
    tokenizer = setup_tokenizer()
    tokenized = tokenizer.tokenize(text)
    return tokenized


@app.route('/', methods=['POST', 'GET'])
def index():
    input_data = parse_input(request)
    if input_data != None:
        #finer = NerFiner(input_data)
        regex = ExecuteRegEx(input_data)
        results, code = regex.run()

        if code == 1:
            data = {'status':200,'data':results, 'service':"Regex Identifier Service, version 1.0-beta", 'date':dt.today().strftime('%Y-%m-%d'), 'version':0.2}
            return jsonify(data)
        else:
            data = {"status":-1,"Error":str(results), "service":"Regex Identifier Service, version 1.0-beta", "date":dt.today().strftime('%Y-%m-%d'), 'version':0.2}
            return jsonify(data)
    data = {"status": -1, "Error": "415 Unsupported Media Type ;)", "service": "Regex Identifier Service",
            "date": dt.today().strftime('%Y-%m-%d'), 'version':0.2}
    return jsonify(data)


#if __name__ == '__main__':
#    app.run(debug=True,port=5000, host='0.0.0.0')
