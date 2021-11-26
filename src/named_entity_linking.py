import subprocess
import fnmatch
import os
from arpa.arpa import Arpa
from datetime import datetime
import json
import sys, math
import logging, zipfile
import re
import traceback
import logging
import time
from datetime import datetime as dt
import datetime

import logging, logging.config

logging.config.fileConfig(fname='conf/logging.ini', disable_existing_loggers=False)
logger = logging.getLogger('arpa')

class ArpaConfig:
    def __init__(self, name="", url="", ordered=False, punct=r'[\.,:;-]{2}', locale="fi"):

        self.arpa_name = name
        self.arpa_url = url
        self.ordered = ordered
        self.punct = r'[\.,:;-]{2}'
        if punct:
            self.punct = punct
        self.locale = "fi"
        if locale:
            self.locale = locale
        else:
            logger.info("got confs: %s, %s, %s, %s", name, url, punct, locale)

    def get_arpa_url(self):
        return self.arpa_url

    def set_arpa_url(self, url):
        self.arpa_url = url

    def get_arpa_name(self):
        return self.arpa_name

    def set_arpa_name(self, name):
        self.arpa_name = name

    def get_ordered(self):
        return self.ordered

    def get_punct(self):
        return self.punct

    def get_locale(self):
        return self.locale

class RunArpaLinker:
    def __init__(self, directory=""):

        self.configs = list()

        # results for all given texts
        self.results = dict()

        self.folder = directory
        if not (self.folder.endswith("/")):
            self.folder += "/"

        self.output_files = list()

    def set_config(self, config):
        if config not in self.configs:
            self.configs.append(config)

    def get_result(self):
        return self.results

    def run_linker(self, input_text):
        arpa_results = dict()

        try:
            #for text, perform arpa queries in predefined order
            for conf in self.configs:
                logger.info("RUN CONF: %s, %s, %s, %s", conf.get_arpa_name(), conf.get_arpa_url(), input_text, conf.get_locale())
                arpa = Arpa(conf.get_arpa_url(), conf.get_ordered())
                punct = conf.get_punct()
                if conf.get_arpa_name() in arpa_results:
                    arpa_results[conf.get_arpa_name()] = arpa_results[conf.get_arpa_name()] + self.do_arpa_query(arpa, input_text, punct,conf.get_locale())
                    logger.info("Updated: %s",arpa_results[conf.get_arpa_name()])
                else:
                    arpa_results[conf.get_arpa_name()] = self.do_arpa_query(arpa, input_text, punct,conf.get_locale())
        except Exception as e:
            logger.warning("Error: %s",e)
            logger.warning(sys.exc_info()[0])
            pass
        return arpa_results

    # Execute arpa queries
    def do_arpa_query(self, arpa, text, punct, locale):
        arpa_results = []
        parts = 0

        triple = dict()
        parts += 1

        logger.debug("Text before modifications: %s", text)
        q = self.stripInput(text, punct)

        if len(q) > 0:
            startTime = dt.now()
            logger.info("query: %s", q)
            result = arpa._query(q, locale)
            if result != None:
                # store the results
                momentum = dt.now()
                now = momentum - startTime
                triple['original'] = text
                triple['querystring'] = q
                triple['arpafied'] = json.loads(result.text)
                arpa_results.append(triple)

        return arpa_results

    # extract results from json to an python array
    def simplify_arpa_results(self, arpafied):
        simplified = dict()
        found = 0  # self.read_stoplist(stopwordlist)
        if arpafied == None:
            return None
        if 'results' in arpafied:
            results = arpafied['results']
            for result in results:
                if 'label' in result:
                    label = result['label']
                    if 'matches' in result:
                        matches = result['matches']
                        # print(matches)
                        for mlabel in matches:
                            # print(mlabel)
                            mlabel = mlabel.replace('"', '')
                            found = found + 1
                            # if mlabel not in simplified and mlabel not in filtered_words:
                            if mlabel not in simplified:
                                # found=found+1
                                labels = list()
                                labels.append(label)
                                simplified[mlabel] = labels
                            else:
                                if label not in simplified[mlabel]:
                                    simplified[mlabel].append(label)

                    elif 'properties' in result and 'ngram' in result['properties']:
                        original_string = result['properties']['ngram'][0]
                        found = found + 1
                        original_string = original_string.replace('"', '')
                        if original_string not in simplified:
                            labels = list()
                            labels.append(label)
                            simplified[original_string] = labels
                        else:
                            if label not in simplified[original_string]:
                                simplified[original_string].append(label)
        #else:
            #logger.warning("Results do not exist in arpafied, " + str(arpafied))
        return simplified, found

    # try to strip special characters and extra spaces from a string
    def stripInput(self, value, punct=r'[\.,:;-]{2}'):
        q = ""
        try:
            stripped = value.strip()
            qstr = stripped.format()
            q = re.sub('\s+', ' ', qstr)
            text = q.replace('*', '').replace('<', '').replace('>', '').replace('^', '').replace("@", '').replace(
                "+", '').replace("?", '').replace("_", '').replace("%", '').replace("'","")
            q = text.replace('§', '').replace('[', '').replace(']', '').replace('{', '').replace("}", '').replace(
                "#", '').replace("~", '').replace('"', '').replace("+", '')
            q = q.replace('@', '').replace('$', '').replace('£', '').replace('µ', '').replace("!", '').replace("&",
                                                                                                               '').replace(
                '=', '').replace("|", '')#.replace(":", '')

            q = q.replace('*', '').replace('^', '').replace("@", '').replace("+", '').replace("?", '').replace("_",
                                                                                                               '').replace(
                "%", '').replace("...", '').replace("|", '').replace("..", '').replace("■", '').replace("£", '')
            q = q.replace('•', '').replace('&', '').replace('´', '').replace('`', '').replace("§", '').replace("½",
                                                                                                               '').replace(
                "=", '').replace('¤', '').replace("$", '').replace("--", '').replace(",,", '').replace("»",
                                                                                                       '').replace(
                "—", '')
            q = q.replace('“', '').replace(' . ', ' ').replace("”", '').replace(".,", '').replace(',.', '').replace(
                "“", '').replace(",,,", '').replace("'", '').replace("«", '')
            q = re.sub(punct, "", q)
            text = re.sub(r'\x85', 'â€¦', text)  # replace ellipses
            text = re.sub(r'\x91', "â€˜", text)  # replace left single quote
            text = re.sub(r'\x92', "â€™", text)  # replace right single quote
            text = re.sub(r'\x93', 'â€œ', text)  # replace left double quote
            text = re.sub(r'\x94', 'â€�', text)  # replace right double quote
            text = re.sub(r'\x95', 'â€¢', text)  # replace bullet
            text = re.sub(r'\x96', '-', text)  # replace bullet
            text = re.sub(r'\x99', 'â„¢', text)  # replace TM
            text = re.sub(r'\xae', 'Â®', text)  # replace (R)
            text = re.sub(r'\xb0', 'Â°', text)  # replace degree symbol
            text = re.sub(r'\xba', 'Â°', text)  # replace degree symbol

            text = re.sub('â€¦', '', text)  # replace ellipses
            text = re.sub('â€¢', '', text)  # replace bullet
            text = re.sub('â– ', '', text)  # replace squares
            text = re.sub('â„¢', '', text)  # replace TM
            text = re.sub('Â®', '', text)  # replace (R)
            text = re.sub('®', '', text)  # replace (R)
            text = re.sub('Â°', '', text)  # replace degree symbol
            text = re.sub('Â°', '', text)  # replace degree symbol

            q = re.sub(r'\d\d.\d\d.\d\d\d\d', "", q)  # dates
            text = re.sub(r'\d{1,2}.\d\d.', "", text)  # times

            # Do you want to keep new lines / carriage returns? These are generally
            # okay and useful for readability
            text = re.sub(r'[\n\r]+', ' ', text)  # remove embedded \n and \r

            #q = re.sub(r'a href \\ \ quot; kb / artikkeli / 319 / \\ \ quot;')


        except ValueError as err:
            logger.warning("Unexpected error while formatting document: %s", err)
            logger.warning("Error document content: %s" + value)
            q = value
        except Exception as e:
            logger.warning("Unexpected error while formatting document: %s", e)
            logger.warning("Error document content: %s" + value)
            q = value
        return q

class NamedEntityLinking:
    def __init__(self, data=None, input_data=None):
        self.folder= "/u/32/tamperm1/unix/python-workspace/nerdl/input/"
        self.linker = RunArpaLinker(directory=self.folder)

    def create_configuration(self, name, url, ordered, punct=None, locales=""):
        if len(url) > 0:
            config=None
            config = ArpaConfig(name, url, ordered, punct=punct, locale=locales)
            self.linker.set_config(config)

    def exec_linker(self, input_text):
        result_data = dict()
        logger.debug("Process documents one by one, one sentence at the time")
        # process documents one by one, one sentence at the time

        if self.linker == None:
            self.linker = RunArpaLinker(self.folder)
        logger.debug("RUN linker")
        resultset=self.linker.run_linker(input_text)
        result = self.parse_results(resultset)
        return result

    def parse_results(self,results):
        result_set = list()
        # parse for each sentence the results of each query
        l = list()
        ecli =""
        # parse and add from each arpa query
        for query_name, query_result in results.items():
            logger.debug(query_name)
            logger.debug(query_result)
            for data in query_result:
                arpafied = data["arpafied"]
                for arpa_result in arpafied['results']:
                    str_label=""
                    str_matches=""
                    ecli_id = ""
                    # now taking only the first result, in near future expand to take it all !
                    properties = arpa_result["properties"]
                    matches = arpa_result["matches"]
                    label = arpa_result["label"]
                    if 'ecli' in properties:
                        ecli_id = str(properties["ecli"][0])

                    if label != None:
                        str_label = label

                    if matches != None:
                        str_matches = matches[0]

                    id = properties["id"][0].replace("<","").replace(">", "")
                    if len(ecli_id)>0:
                        ecli = ecli_id.replace("\"","")
                    else:
                        ecli = ""
                    logger.info("Add triple: %s, %s, %s, %s, %s", str_matches, str_label, id, ecli,ecli_id)
                    result_set.append((str_matches, str_label, id, query_name, ecli))
        return result_set