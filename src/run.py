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

app = Flask(__name__)

@app.before_request
def before_request():
    if True:
        print("HEADERS", request.headers)
        print("REQ_path", request.path)
        print("ARGS",request.args)
        print("DATA",request.data)
        print("FORM",request.form)

def parse_input(request):
    input = None
    if request.method == 'GET':
        text = request.args.get('text')
        sentences = tokenization(text)
        print("tokenization results",sentences)
        input = {i: sentences[i] for i in range(0, len(sentences))}
        print("data", input)
    else:
        if request.headers['Content-Type'] == 'text/plain':
            print("input:", request.data.decode('utf-8'))
            sentences = tokenization(str(request.data.decode('utf-8')))
            input = {i:sentences[i] for i in range(0, len(sentences))}
            print("data", input)
        else:
            print("Bad type", request.headers['Content-Type'])
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
    print('Tokenize this SHIT:', text, tokenized)
    return tokenized


@app.route('/', methods=['POST', 'GET'])
def index():
    print("APP name",__name__)
    input_data = parse_input(request)
    if input_data != None:
        #finer = NerFiner(input_data)
        regex = ExecuteRegEx(input_data)
        results, code = regex.run()

        if code == 1:
            print('results',results)
            data = {'status':200,'data':results, 'service':"Regex Identifier Service", 'date':dt.today().strftime('%Y-%m-%d'), 'version':0.2}
            return jsonify(data)
        else:
            data = {"status":-1,"Error":str(results), "service":"Regex Identifier Service", "date":dt.today().strftime('%Y-%m-%d'), 'version':0.2}
            return jsonify(data)
    data = {"status": -1, "Error": "415 Unsupported Media Type ;)", "service": "Regex Identifier Service",
            "date": dt.today().strftime('%Y-%m-%d'), 'version':0.2}
    return jsonify(data)


#if __name__ == '__main__':
#    app.run(debug=True,port=5000, host='0.0.0.0')