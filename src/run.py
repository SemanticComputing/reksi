from flask import Flask
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
            sentences = tokenization(str(request.data.decode('utf-8')))
            input = {i:sentences[i] for i in range(0, len(sentences))}
            print("data", input)
        else:
            print("Bad type", request.headers['Content-Type'])
    return input

def tokenization(text):
    print('Tokenize this', text)
    tokenizer = nltk.data.load('tokenizers/punkt/finnish.pickle')
    return tokenizer.tokenize(text)


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
            data = {"status":200,"data":str(results), "service":"Regex Identifier Service", "date":dt.today().strftime('%Y-%m-%d')}
            return json.dumps(data, ensure_ascii=False)
        else:
            data = {"status":-1,"Error":str(results), "service":"Regex Identifier Service", "date":dt.today().strftime('%Y-%m-%d')}
            return json.dumps(data, ensure_ascii=False)
    return "415 Unsupported Media Type ;)"


#if __name__ == '__main__':
#    app.run(debug=True,port=5000, host='0.0.0.0')