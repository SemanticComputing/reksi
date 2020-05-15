import subprocess
import fnmatch
import os, re
import ntpath
import logging
import os.path
from pathlib import Path
import configparser
from dateparser.search import search_dates
from named_entity_linking import NamedEntityLinking
import nltk, nltk.data
from DateConverter import *
DateConverter.OUTFORMAT="times:time_{}-{}"

import logging, logging.config

logging.config.fileConfig(fname='conf/logging.ini', disable_existing_loggers=False)
logger = logging.getLogger('reksi')

class PatternLib:
    def __init__(self, config):
        self.config = config
        self.configs = dict()
        self.arpas = dict()
        self.arpa_locales=dict()
        self.read_configs()

    def get_patterns(self):
        return self.configs

    def get_arpas(self, pattern=""):
        if len(pattern)>0:
            if pattern in self.arpas.keys():
                return self.arpas[pattern]
        else:
            return self.arpas
        return None

    def get_arpa_locales(self, arpas=list()):
        locales=list()
        if len(arpas)>0:
            for arpa in arpas:
                if arpa in self.arpa_locales.keys():
                    locales.extend(self.arpa_locales[arpa])
        return set(locales)
    '''
    Reads configuration file and extracts settings for pattern library.
    '''
    def read_configs(self):
        config = configparser.RawConfigParser()
        config.read(self.config)
        for pattern in config.sections():
            # read regex patterns
            if pattern not in self.configs: # and len(config[pattern]['pattern']) > 0:
                self.configs[pattern] = self.parse_regex_patterns(config[pattern])
            else:
                if len(config[pattern]['pattern']) > 0:
                    logger.info("Pattern %s found in configs: %s", str(pattern),str(self.configs))
                    logger.info("Suggested value %s not added because of old value: %s", str(config[pattern]['pattern']), str(self.configs[pattern]))
            if pattern not in self.arpas and len(config[pattern]['arpa']) > 0:
                self.arpas[pattern] = config[pattern]['arpa']
                if self.arpas[pattern] not in self.arpa_locales and len(config[pattern]['locale']) > 0:
                    self.arpa_locales[self.arpas[pattern]] =config[pattern]['locale'].split(',')
                else:
                    if self.arpas[pattern] not in self.arpa_locales:
                        self.arpa_locales[self.arpas[pattern]] =list("fi")
            else:
                if len(config[pattern]['arpa']) > 0:
                    logger.info("Pattern %s found in ARPAs: %s", str(pattern), str(self.arpas))
                    logger.info("Suggested value %s not added because of old value: %s", str(config[pattern]['arpa']), str(self.arpas[pattern]))

    def parse_regex_patterns(self, conf):
        i = 9999
        listing = list()
        for j in range(1, i):
            pattern = 'pattern' + str(j)
            if pattern in conf and len(conf[pattern])>0:
                listing.append(conf[pattern])

        return listing

# class DateIdentifier:
#     def __init__(self):
#         pass


class MatchEntity:
    def __init__(self, name="", type="", start=-1, end=-1, arpas=None, locales=None):
        self.type = type
        self.end_ind = end
        self.start_ind = start
        self.name = name
        self.data_id = ""
        self.locales = None
        if arpas != None:
            logger.info("ADDING ARPAS: %s", arpas)
            self.arpas=arpas.split(',')
        else:
            self.arpas = list()
        if locales != None:
            logger.info("ADDING LOCALEs %s", locales)
            self.locales = locales
        else:
            self.locales = list("fi")
        self.links=list()
        logger.info('create entity: %s, %s, %s-%s', name, type, start, end)

    def get_type(self):
        return self.type

    def get_end_index(self):
        return self.end_ind

    def get_start_index(self):
        return self.start_ind

    def get_name(self):
        return self.name

    def get_length(self):
        return self.end_ind - self.start_ind

    def get_arpa(self):
        return self.arpas

    def get_locales(self):
        return self.locales

    def set_alt_id(self, idx):
        if idx != None and len(idx)>0:
            self.data_id = idx

    def get_alt_id(self):
        return self.data_id

    def jsonify(self):
        link = dict()
        for tpl in self.links:
            link = tpl[0]
            endpoint = tpl[1]
            query = tpl[2]
            eplink = str(query) + '-links'
        return {'entity':self.name, 'category':self.type, 'start_index':self.start_ind, 'end_index':self.end_ind, 'links':','.join(self.links), 'alternate_id':self.get_alt_id()}

    def set_link(self, links=None):
        if links != None:
            self.links=links

    def add_link_data(self, data):
        for tpl in data:
            match = tpl[0]
            label = tpl[1]
            link = tpl[2]
            query_name = tpl[3]
            ecli = tpl[4]

            self.set_alt_id(ecli)

            logger.info("Adding link: %s, %s, %s, %s", link, label, match, query_name)
            if link not in self.links:
                self.links.append(link)

    def overlap_comparison(self, other):
        # check if number in range
        x = range(self.start_ind, self.end_ind)
        y = range(other.get_start_index(), other.get_end_index())
        xs = set(x)
        intersect = xs.intersection(y)
        if len(intersect) > 0:
            return True
        return False

    def __str__(self):
        return self.name + " : " + str(self.start_ind) + "," + str(self.end_ind) + " (" + self.type +")"

    def __repr__(self):
        return str(self)

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

    def __len__(self):
        return int(self.get_length())

    def __hash__(self):
        return hash(repr(self))


class PatternFinder:
    def __init__(self):
        self.languages = ['sv', 'fi']
        self.patterns = PatternLib('conf/app_config.ini')

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

        rdp = search_dates(text, languages=self.languages, settings={'SKIP_TOKENS': []})
        rdc = DateConverter.find(text)
        r = list()
        r2 = list()
        if rdp != None:
            r = [str(item[0]) for item in rdp]
            logger.debug("search_dates: %s", rdp)
        if rdc != None:
            r2 = [str(item.split(',')[1].replace('"', '')) for item in rdc]
            logger.debug("DateConverter: %s",rdc)
        r.extend(r2)

        if r is not None:
            logger.debug("dates: %s",r)
            for result in r:
                logger.debug('iterate: %s', result)
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
                                    logger.debug('REplacing %s with %s', results[code], add_me)
                                    results[code] = add_me

                                    #i = i+1
                                elif results[code] == add_me:
                                    logger.debug('Already exists, overlapp checked: %s', add_me)

                            else:
                                # new value
                                results[i] = m
                                i = i + 1
                        else:
                            results[i] = m
                            i = i+1
                    else:
                        logger.info('Already exits: %s', m)

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

    return list of position tuples (start index, end index)
    '''
    def find_place(self, str, text):
        logger.debug("Search for %s in %s", str, text)
        positions = [(m.start(), m.end()) for m in re.finditer(str, text)]
        logger.debug('FOUND positions: %s, %s, %s',positions, str, text)
        return positions

    '''
    Identifies information using regex patterns.
    @text - text where the information is searched from
    @patterns - dictionary of regex patterns

    return dictionary of results
    '''
    def identify_regex_patterns(self, text):
        i = 0
        results = dict()
        patterns = self.patterns.get_patterns()
        arpas = self.patterns.get_arpas()
        for id, all_patterns in patterns.items():
            for pattern in all_patterns:
                logger.debug("Using pattern %s to find from text %s this: %s", pattern, text, id)
                matches = re.finditer(pattern, text)
                arpa = None
                locale=None

                for match in matches:
                    if id in arpas:
                        arpa = arpas[id]
                        if arpa != None:
                            locale = list(self.patterns.get_arpa_locales(arpa.split(',')))
                    logger.info("%s, %s, %s",id, match.span(), match.group())
                    s = match.span()[0]
                    e = match.span()[1]
                    m = MatchEntity(name=match.group(), type=id, start=s, end=e, arpas=arpa, locales=locale)
                    if m not in results.values():
                        results[i] = m
                        i += 1

        logger.info(results)
        return results


class ExecuteRegEx:
    def __init__(self, data):
        self.texts = data
        self.words = dict()
        self.finder = PatternFinder()

    '''
    Run regex finder.

    return json of results
    '''
    def run(self):
        jsonresult = None
        data = None
        results = dict()

        for id,text in self.texts.items():
            logger.info('Text: %s', text)
            jsonresult = {'sentence':id+1, 'text':text}

            dates = self.finder.identify_dates(text)
            if dates != None:
                logger.info('Dates: %s', dates)
            regex = self.finder.identify_regex_patterns(text)
            if regex != None:
                logger.info('Others: %s', regex)

            entities = self.disambiguate(dates, regex)
            self.link_entities(entities)
            data = self.jsonify_results(entities, data)

            logger.info("DATA: %s", data)

            #print('dates', dates)
            #if dates != None:
            #    data = self.jsonify_results(dates, data)

            #print('others', regex)
            #if regex != None:
            #    data = self.jsonify_results(regex, data)

            if jsonresult != None:
                jsonresult["entities"] = data
                results[(id+1)]=jsonresult
                jsonresult = None
                data = None
            else:
                jsonresult = None
                data = None

        return results, 1

    def link_entities(self, entities):
        logger.info("START TO LINK: %s", entities)

        punct = None
        for entity in entities:
            arpas = entity.get_arpa()
            locales = entity.get_locales()
            linker = NamedEntityLinking()
            if len(arpas) > 0:
                for url in arpas:
                    for locale in locales:
                        logger.info("LINKIN: %s, %s, %s, %s",entity.get_type(), url, entity.get_name(), locale)
                        if entity.get_type()=="COURT_DECISION":
                            punct=r'[\.,;-]{2}'
                        else:
                            punct=None

                        arpaname = url.split('/')[-1]
                        linker.create_configuration(arpaname, url, False, punct, locale)
                result = linker.exec_linker(entity.get_name())
                logger.info(result)
                entity.add_link_data(result)
            else:
                logger.info("NO ARPAS to print")

    def overlap(self, itemsA, itemsB):
        overlapping = dict()
        clear = list()
        logger.info("Check overlap: %s, %s", itemsA, itemsB)
        for itemA in itemsA.values():
            if len(itemsB) > 0:
                for itemB in itemsB.values():
                    overlap = itemA.overlap_comparison(itemB)
                    logger.info("Overlap? %s %s %s", itemA, itemB, overlap)
                    if overlap:
                        if itemA not in overlapping.keys():
                            overlapping[itemA]=list()

                        if itemB not in overlapping[itemA]:
                            overlapping[itemA].append(itemB)
                if itemA not in overlapping.keys() and itemA not in clear:
                    logger.info("Clearing: %s", itemA)
                    clear.append(itemA)
        return clear, overlapping

    def combine_overlapping(self, itemsA, itemsB):
        overlap = dict()
        for key, overlapping_items in itemsA.items():
            if key not in overlap.keys():
                overlap[key] = overlapping_items

        for key, overlapping_items in itemsB.items():
            if key not in overlap.keys():
                overlap[key] = overlapping_items

        return overlap

    # def check_values_in_list(self, value, itemlist):
    #     collectables = list()
    #     for v in value:
    #         if v not in itemlist:
    #             collectables.append(v)
    #     return collectables

    def disambiguate(self, itemsA, itemsB):
        clear = list()
        if itemsA != None and itemsB != None:
            if len(itemsA) > 0 and len(itemsB) > 0:
                logger.info("Have to check disambiguation")
                clearA, overlappingA = self.overlap(itemsA, itemsB)
                clearB, overlappingB = self.overlap(itemsB, itemsA)

                clear = clearA + clearB
                overlapping = self.combine_overlapping(overlappingA, overlappingB)

                logger.debug("Clear: %s", clear)
                logger.debug("Overlapping: %s", overlapping)

                for key, value_list in overlapping.items():
                    longest = max(value_list, key=len)
                    if len(key) > len(longest):
                        if key not in clear:
                            clear.append(key)
                    else:
                        if longest not in clear:
                            clear.append(longest)

            else:
                logger.info("No need to disambiguate")
                if len(itemsA) > 0:
                    logger.debug(itemsA)
                    clear = self.extract_list(itemsA)
                elif len(itemsB) > 0:
                    logger.debug(itemsB)
                    clear = self.extract_list(itemsB)
        else:
            logger.info("No need to disambiguate")
            if itemsA != None:
                clear = self.extract_list(itemsA)
            elif itemsB != None:
                clear = self.extract_list(itemsB)

        logger.debug("Result: %s", clear)
        return clear

    def extract_list(self, result):
        result_array = list()
        if type(result) == dict:
            result_array = list(result.values())
        elif type(result) == list:
            result_array = result

        return result_array

    def jsonify_results(self, result, result_array):
        logger.debug("convert to json: %s",result)
        if result_array == None:
            result_array = []
        if type(result) == dict:
            for id, item in result.items():
                j = item.jsonify()
                if j not in result_array:
                    result_array.append(j)
        elif type(result) == list:
            for item in result:
                j = item.jsonify()
                if j not in result_array:
                    result_array.append(j)

        return result_array

    # '''
    # Tokenize text to words
    # '''
    # def tokenization(self):
    #     tokenizer = nltk.data.load('tokenizers/punkt/finnish.pickle')
    #     for id, text in self.texts.items():
    #         logger.info('Tokenize this: %s', text)




