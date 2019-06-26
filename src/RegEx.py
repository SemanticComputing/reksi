import subprocess
import fnmatch
import os, re
import ntpath
import logging
import os.path
from pathlib import Path
import configparser
from dateparser.search import search_dates
import nltk, nltk.data
from DateConverter import *
DateConverter.OUTFORMAT="times:time_{}-{}"

class PatternLib:
    def __init__(self, config):
        self.config = config
        self.configs = dict()
        self.read_configs()

    def get_patterns(self):
        return self.configs

    '''
    Reads configuration file and extracts settings for pattern library.
    '''
    def read_configs(self):
        config = configparser.RawConfigParser()
        config.read(self.config)
        for pattern in config.sections():
            if pattern not in self.configs and len(config[pattern]['pattern']) > 0:
                self.configs[pattern] = config[pattern]['pattern']
            else:
                if len(config[pattern]['pattern']) > 0:
                    print("Pattern ", str(pattern), " found in configs: ", str(self.configs))
                    print("Suggested value ", str(config[pattern]['pattern']), " not added because of old value: ", str(self.configs[pattern]))


class DateIdentifier:
    def __init__(self):
        pass

class MatchEntity:
    def __init__(self, name="", type="", start=-1, end=-1):
        self.type = type
        self.end_ind = end
        self.start_ind = start
        self.name = name
        print('create entity', name, type, start, end)

    def get_type(self):
        return self.type

    def get_end_index(self):
        return self.end_ind

    def get_start_index(self):
        return self.start_ind

    def get_name(self):
        return self.name

    def jsonify(self):
        # {"status": 200, "data": "{'0': [{'entity': ' Nokia', 'type': 'CorporationsName', 'word_start_index': 1, 'word_end_index': 1}]}"}
        return {'entity':self.name, 'category':self.type, 'start_index':self.start_ind, 'end_index':self.end_ind}

    def __str__(self):
        return self.name + " : " + str(self.start_ind) + "," + str(self.end_ind) + " (" + self.type +")"

    def __eq__(self, other):
        if self.name != other.get_name():
            return False
        if self.type != other.get_type():
            return False
        if self.start_ind != other.get_start_index():
            return False
        if self.end_ind != other.get_end_index():
            return False

        return True

    def __ne__(self, other):
        if self.name == other.get_name():
            return False
        if self.type == other.get_type():
            return False
        if self.start_ind == other.get_start_index():
            return False
        if self.end_ind == other.get_end_index():
            return False

        return True


class PatternFinder:
    def __init__(self):
        self.languages = ['sv', 'fi']
        self.patterns = PatternLib('src/config.ini')

        DateConverter.OUTFORMAT = '{}-{},"{}"'
        DateConverter.MINTIME = datetime.date(200, 1, 1)

    '''
    Identifies references to dates using dateparser.
    @text - text where the dates are searched from
    
    return dictionary of results example: [('Thursday', datetime.datetime(2018, 9, 27, 0, 0))]
    '''
    def identify_dates(self, text):
        results = dict()
        i = 0

        #rdp = search_dates(text, languages=self.languages, settings={'SKIP_TOKENS': []})
        rdc = DateConverter.find(text)
        r = list()
        r2 = list()
        #if rdp != None:
        #    r = [str(item[0]) for item in rdp]
        #    print("search_dates:", rdp)
        if rdc != None:
            r2 = [str(item.split(',')[1].replace('"', '')) for item in rdc]
            print("DateConverter:",rdc)
        r.extend(r2)

        if r is not None:
            print("dates",r)
            for result in r:
                print('iterate', result)
                positions = self.find_place(result, text)
                for start, end in positions:
                    m = MatchEntity(name=result, type="DATETIME", start=start, end=end)
                    if m not in results.values():
                        # find out if there is an overlap between entity indeces
                        if len(results) > 0:
                            add_me, code = self.find_overlapp_indeces(m, results)
                            if code > -1:
                                # replace with a better alternative, or same if everything matches
                                if add_me not in results.values():
                                    print('REplacing', results[code], ' with ', add_me)
                                    results[code] = add_me

                                    #i = i+1
                                elif  results[code] == add_me:
                                    print('Already exists, overlapp checked', add_me)

                            else:
                                # new value
                                results[i] = m
                                i = i + 1
                        else:
                            results[i] = m
                            i = i+1
                    else:
                        print('Already exits', m)

        return results

    '''
    Identify overlapping strings from text that have overlapping locations.
    @entity - object that is being compared to objects in a list of objects
    @item - a list of objects

    return object and index
    '''
    def find_overlapp_indeces(self, entity, lst):
        for i, item in lst.items():
            if item.get_start_index() == entity.get_start_index():
                if item.get_end_index() == entity.get_end_index():
                    # in case there is an identical match, index vice
                    return item, i
                else:
                    # return larger entity of the two
                    return self.get_larger_entity(entity, item), i
            # if the indexes do not overlap, but are smaller
            elif item.get_start_index() < entity.get_start_index() and item.get_start_index() < entity.get_end_index():
                pass
            elif item.get_start_index() > entity.get_end_index() and item.get_end_index() > entity.get_end_index():
                pass
            else:
                # start indeces differ but the end indeces indicate overlap, return the larger one
                if item.get_end_index() == entity.get_end_index():
                    return self.get_larger_entity(entity, item), i
                else:
                    return self.get_larger_entity(entity, item), i
        return entity, -1

    '''
    Measure which entity has a longer string and return the longer one.
    @entity - object being compared to...
    @item - item from a list of items

    return object with a longer string
    '''
    def get_larger_entity(self, entity, item):
        # nothing should happen
        if len(item.get_name()) > len(entity.get_name()):
            return item
        else:
            # replace the existing item with a larger item
            return entity

    '''
    Locates the position of the string in text.
    @str - string that is being searched
    @text - text where the information is searched from

    return list of position tupples (start index, end index)
    '''
    def find_place(self, str, text):
        print("Search for", str, "in", text)
        positions = [(m.start(), m.end()) for m in re.finditer(str, text)]
        print('FOUND positions: ',positions, str, text)
        for start, end in positions:
            print("POSITION: ",start, end, text[start:end])
        return positions

    '''
    Identifies information using regex patterns.
    @text - text where the information is searched from
    @patterns - dictionary of regex patterns

    return dictionary of results
    '''
    def identify_regex_patterns(self, text):
        results = list()
        patterns = self.patterns.get_patterns()
        for id, pattern in patterns.items():
            #matches = re.findall(pattern, text)
            print("Using pattern", pattern, " to find from text ", text, " this: ", id)
            matches = re.finditer(pattern, text)

            for match in matches:
                print(id, match.span(), match.group())
                s = match.span()[0]
                e = match.span()[1]
                m = MatchEntity(name=match.group(), type=id, start=s, end=e)
                if m not in results:
                    results.append(m)

        print(results)
        return results

class ExecuteRegEx:
    def __init__(self, data):
        self.texts = data
        self.words = dict()
        self.finder = PatternFinder()
        #self.tokenization()

    '''
    Run regex finder.

    return json of results
    '''
    def run(self):
        jsonresult = None
        data = None
        results = dict()

        for id,text in self.texts.items():
            print('Text: ', text)
            jsonresult = {'sentence':id, 'text':text}

            dates = self.finder.identify_dates(text)
            print('dates', dates)
            if dates != None:
                data = self.jsonify_results(dates, data)

            regex = self.finder.identify_regex_patterns(text)
            print('others', regex)
            if regex != None:
                data = self.jsonify_results(regex, data)

            if jsonresult != None:
                #if 'entities' not in jsonresult:
                jsonresult["entities"] = data
                results[id]=jsonresult
                jsonresult = None
                data = None
            else:
                jsonresult = None
                data = None

        return results, 1

    def jsonify_results(self, result, result_array):
        print("convert to json: ",result)
        if result_array == None:
            result_array = []
        if type(result) == dict:
            for id, item in result.items():
                result_array.append(item.jsonify())
        elif type(result) == list:
            for item in result:
                result_array.append(item.jsonify())

        return result_array

    '''
    Tokenize text to words
    '''
    def tokenization(self):
        tokenizer = nltk.data.load('tokenizers/punkt/finnish.pickle')
        for id, text in self.texts.items():
            print('Tokenize this', text)
            #self.words[id] = [tokenizer.word_tokenize(i) for i in text]

        #return tokenizer.tokenize(text)



