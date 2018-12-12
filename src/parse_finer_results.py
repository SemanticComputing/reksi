from run_finer import RunFiner
from namedentity import NamedEntity
import os, json
import logging

logger = logging.getLogger('Finer')
hdlr = logging.FileHandler('finer.log')
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.INFO)

class NerFiner:
    def __init__(self, text_data):
        self.input_data = text_data #self.create_ner_input_data(data)
        self.orig_data = None #data

    def run_finer(self):
        finerParser = ParseFinerResults()
        finer = RunFiner("/u/32/tamperm1/unix/git/finer-wrapper/src/", "*.txt", "", self.input_data)

        texts, codes = finer.run()
        print(texts, codes)

        finerParser.parse_string(texts, finer.get_output_files())
        if finerParser.get_error() == None:
            nes = finerParser.get_json_string()
            return nes, 1
        else:
            return self.get_errors_json(finerParser,finer), 0

    #def get_errors_json(self):

    def create_ner_input_data(self,s):
        data = dict()
        for struct in s.get_structures():
            head, structu_id = os.path.split(struct.get_structure_id())
            for parid, parval in struct.get_paragraphs().items():

                for sid, sentence in parval.get_sentences().items():
                    ind = str(structu_id) + "_" + str(parid) + "_" + str(sid)
                    data[ind] = " ".join([word.get_word() for word in list(sentence.get_words().values())])

        return data

    def write_nes(self, nes):
        STRUCT_ID = 0
        PAR_ID = 1
        SEN_ID = 2
        for ne in nes.keys():
            split = ne.split("_")
            structid = split[STRUCT_ID]
            parid = split[PAR_ID]
            senid = split[SEN_ID]

            structures = self.orig_data.get_structures()
            for struct in structures:
                head, structu_id = os.path.split(struct.get_structure_id())
                if structu_id == structid:
                    paragraph = struct.get_paragraph(parid)
                    sentence = paragraph.get_sentence(senid)
                    #print("string, ",nes[ne].get_string())
                    start, end = sentence.find_word_ind(nes[ne].get_string().strip().split())
                    if start == None and end == None:
                        start, end = sentence.find_word_ind(list(reversed(nes[ne].get_string().strip().split())))

                    if start == None and end == None:
                        start, end = sentence.find_word_ind(nes[ne].get_string().strip().replace("."," .").split())

                    if start != None and end != None:
                        nes[ne].set_start_ind(start)
                        nes[ne].set_end_ind(end)
                        sentence.add_ne(nes[ne])
                    else:
                        logging.warning("Could not find ne %s %s", str(nes[ne]), nes[ne].get_string().strip().replace(".", " ."))
                        logging.warning("For sentence %s", str(sentence.get_words()))
                        #logging.warning("From pool of ne %s", str(nes))

    def get_data(self):
        return self.orig_data

    def get_errors_json(self, parser, finer):
        errors = list()
        for err in parser.get_error():
            errors.append(finer.get_error_json(err))
        return json.dumps(errors, ensure_ascii=False)

class ParseFinerResults:
    def __init__(self):
        self.error = None
        self.tags = NerTags()
        self.nes = dict()
        self.ne_json = dict()
        self.ne_type_labels = {"EnamexOrgCrp": "OrganizationName", "EnamexPrsHum": "PersonName",
                               "TimexTmeDat": "ExpressionTime", "EnamexLocXxx": "PlaceName",
                               "EnamexLocStr": "AddressName", "EnamexLocPpl": "PoliticalLocation",
                               "EnamexLocGpl": "GeographicalLocation", "EnamexOrgEdu": "EducationalOrganization",
                               "EnamexOrgCrp": "CorporationsName", "EnamexOrgAth":"SportsOrganizations",
                               "EnamexOrgClt":"CultureOrganization", "EnamexOrgPlt":"PoliticalOrganization",
                               "EnamexOrgTvr":"MediaOrganization", "EnamexPrsTit":"Title", "EnamexOrgFin": "FinnishOrganization",
                               "Exc":"Executive", "Event":"Event"}

    def get_error(self):
        return self.error

    def parse_string(self, texts, files):
        from io import StringIO
        import xml.dom.minidom
        import xml.etree.ElementTree as ET
        openTag = False
        recordNer = dict()
        ind = 0
        for i in texts:
            s = StringIO(texts[i])
            for line in s:
                if line.startswith('<?xml version="1.0" encoding="utf-8"?>'):
                    if self.error == None:
                        self.error = dict()
                    self.error[i] = texts[i]
                    print("Error", texts[i])
                    continue
                if "<title>500 Internal Server Error</title>" in line:
                    if self.error == None:
                        self.error = dict()
                    self.error[i] = texts[i]
                    print("Error", texts[i])
                    continue
                if len(line) > 1:
                    file = files[i]
                    line_arr = line.replace("\n", "").split("\t")
                    #print("LINE", line)
                    #print("LINE_ARR", line_arr)
                    for l in line_arr:
                        if "<" in l and openTag == False:
                            start = self.tags.is_ner_start_tag(l)
                            single = self.tags.is_ner_single_tag(l)
                            #print("start, single ?", start, single, recordNer)
                            if start != None:
                                openTag = True
                                recordNer[ind] = line_arr[0]
                            elif single != None:
                                recordNer[ind] = line_arr[0]
                                self.save_ne(recordNer, file, single)
                                recordNer = dict()
                            elif single == None and start == None:
                                logging.warning("Unidentified tag: %s", line_arr)
                        elif "<" in l and openTag == True:
                            end = self.tags.is_ner_end_tag(l)
                            if end != None:
                                #print("close", start, end, recordNer)
                                openTag = False
                                self.save_ne(recordNer, file, end)
                                recordNer = dict()
                        elif ("<" not in l and ">" not in l) and openTag == True:
                            val = l.strip()
                            if len(val) > 1:
                                recordNer[ind] = val
                ind +=1

    def parse_nes(self, ind, file, line_arr):
        openTag = False
        recordNer = dict()
        if len(line_arr) > 1:
            print("LINE_ARR",line_arr)
            for l in line_arr:
                if "<" in l and openTag == False:
                    start = self.tags.is_ner_start_tag(l)
                    single = self.tags.is_ner_single_tag(l)
                    print("start, single ?",start, single)
                    if start != None:
                        openTag = True
                        recordNer[ind] = line_arr[0]
                    elif single != None:
                        recordNer[ind] = line_arr[0]
                        self.save_ne(recordNer, file, single)
                        recordNer = dict()
                    elif single == None and start == None:
                        logging.warning("Unidentified tag: %s", line_arr)
                elif "<" in l and openTag == True:
                    end = self.tags.is_ner_end_tag(l)
                    if end != None:
                        openTag = False
                        self.save_ne(recordNer, file, end)
                        recordNer = dict()
                elif ("<" not in l and ">" not in l) and openTag == True:
                    val = l.strip()
                    if len(val) > 1:
                        recordNer[ind] = val
        else:
            print("Cannot split line", line, line_arr)

    def parse_file(self, files):
        import xml.dom.minidom
        openTag = False
        recordNer = dict()

        for file in files:
            #print(file)
            with open(file) as f:
                for ind, line in enumerate(list(f)):
                    #print(str(line.split("\t")))
                    line_arr = line.replace("\n","").split("\t")
                    if line.startswith('<?xml version="1.0" encoding="utf-8"?>'):
                        f.closed
                        if self.error == None:
                            self.error = dict()
                        self.error[ind] = xml.dom.minidom.parse(file)
                    if len(line_arr)>1:
                        for l in line_arr:
                            if "<" in l and openTag == False:
                                start = self.tags.is_ner_start_tag(l)
                                single = self.tags.is_ner_single_tag(l)
                                if start != None:
                                    openTag = True
                                    recordNer[ind] =line_arr[0]
                                elif single != None:
                                    recordNer[ind] = line_arr[0]
                                    self.save_ne(recordNer, file, single)
                                    recordNer = dict()
                                elif single == None and start == None:
                                    logging.warning("Unidentified tag: %s", line_arr)
                            elif "<" in l and openTag == True:
                                end = self.tags.is_ner_end_tag(l)
                                if end != None:
                                    openTag = False
                                    self.save_ne(recordNer, file, end)
                                    recordNer = dict()
                            elif ("<" not in l and ">" not in l) and openTag == True:
                                val = l.strip()
                                if len(val) > 1:
                                    recordNer[ind] = val
                                    #logging.info("Add %s to %s",val , ind)


            f.closed
            #print(redordNer)

    # saving each ne into a dict with a key (structure_paragraph_sentence_#word#ids)
    def save_ne(self, ner, file, tag):

        first_ind = list(ner.keys())[0]
        last_ind = list(ner.keys())[-1]
        value = ""
        path, fname = os.path.split(file)
        name = os.path.splitext(fname)[0]
        for n in ner.keys():
            name += "#" + str(n)
            value += " " + str(ner[n])

        ne = NamedEntity()
        #logging.info("Saving NE: %s (%s : %s)", value, first_ind, last_ind)
        ne.set_ne("", value, first_ind, last_ind, self.ne_type_labels[tag], "finer")
        ne.add_score("method", 1)
        #logging.info("Saving ne %s = %s : %s", str(ne.get_string()), str(first_ind), str(last_ind))
        self.nes[name] = ne
        if os.path.splitext(fname)[0] not in self.ne_json:
            self.ne_json[os.path.splitext(fname)[0]] = list()
        self.ne_json[os.path.splitext(fname)[0]].append(ne.json())



    def get_nes(self):
        return self.nes

    def get_json_string(self):
        return self.ne_json #.encode('utf-8')

class NerTags:
    def __init__(self):
        self.tags_start = dict()
        self.tags_end = dict()
        self.single_tags = dict()

        # company, society, union etc
        self.tags_start["EnamexOrgCrp"] = "<EnamexOrgCrp>"
        self.tags_end["EnamexOrgCrp"] =  "</EnamexOrgCrp>"

        # Henkilö
        self.tags_start["EnamexPrsHum"] =  "<EnamexPrsHum>"
        self.tags_end["EnamexPrsHum"] =  "</EnamexPrsHum>"
        self.single_tags["EnamexPrsHum"] =  "<EnamexPrsHum/>"

        # Ajan ilmaus: pvm
        self.tags_start["TimexTmeDat"] =  "<TimexTmeDat>"
        self.tags_end["TimexTmeDat"] =  "</TimexTmeDat>"
        self.single_tags["TimexTmeDat"] =  "<TimexTmeDat/>"

        # general location
        self.tags_start["EnamexLocXxx"] =  "<EnamexLocXxx>"
        self.tags_end["EnamexLocXxx"] =  "</EnamexLocXxx>"
        self.single_tags["EnamexLocXxx"] =  "<EnamexLocXxx/>"

        # street, road, street address
        self.tags_start["EnamexLocStr"] =  "<EnamexLocStr>"
        self.tags_end["EnamexLocStr"] =  "</EnamexLocStr>"
        self.single_tags["EnamexLocStr"] =  "<EnamexLocStr/>"

        # political location(state, city etc.)
        self.tags_start["EnamexLocPpl"] =  "<EnamexLocPpl>"
        self.tags_end["EnamexLocPpl"] =  "</EnamexLocPpl>"
        self.single_tags["EnamexLocPpl"] =  "<EnamexLocPpl/>"

        # geographical location
        self.tags_start["EnamexLocGpl"] =  "<EnamexLocGpl>"
        self.tags_end["EnamexLocGpl"] =  "</EnamexLocGpl>"
        self.single_tags["EnamexLocGpl"] =  "<EnamexLocGpl/>"

        # educational organization
        self.tags_start["EnamexOrgEdu"] =  "<EnamexOrgEdu>"
        self.tags_end["EnamexOrgEdu"] =  "</EnamexOrgEdu>"
        self.single_tags["EnamexOrgEdu"] =  "<EnamexOrgEdu/>"

        # Corporations, associations etc.
        self.tags_start["EnamexOrgCrp"] = "<EnamexOrgCrp>"
        self.tags_end["EnamexOrgCrp"] = "</EnamexOrgCrp>"
        self.single_tags["EnamexOrgCrp"] = "<EnamexOrgCrp/>"

        # Athletic/sports organizations
        self.tags_start["EnamexOrgCrp"] = "<EnamexOrgCrp>"
        self.tags_end["EnamexOrgCrp"] = "</EnamexOrgCrp>"
        self.single_tags["EnamexOrgCrp"] = "<EnamexOrgCrp/>"

        # Cultural organizations
        self.tags_start["EnamexOrgClt"] = "<EnamexOrgClt>"
        self.tags_end["EnamexOrgClt"] = "</EnamexOrgClt>"
        self.single_tags["EnamexOrgClt"] = "<EnamexOrgClt/>"

        # Political parties
        self.tags_start["EnamexOrgPlt"] = "<EnamexOrgPlt>"
        self.tags_end["EnamexOrgPlt"] = "</EnamexOrgPlt>"
        self.single_tags["EnamexOrgPlt"] = "<EnamexOrgPlt/>"

        # Media organizations (TV, radio, press)
        self.tags_start["EnamexOrgTvr"] = "<EnamexOrgTvr>"
        self.tags_end["EnamexOrgTvr"] = "</EnamexOrgTvr>"
        self.single_tags["EnamexOrgTvr"] = "<EnamexOrgTvr/>"

        # A title possibly preceding a personal name
        self.tags_start["EnamexPrsTit"] = "<EnamexPrsTit>"
        self.tags_end["EnamexPrsTit"] = "</EnamexPrsTit>"
        self.single_tags["EnamexPrsTit"] = "<EnamexPrsTit/>"

        # A finnish organization (banks)
        self.tags_start["EnamexOrgFin"] = "<EnamexOrgFin>"
        self.tags_end["EnamexOrgFin"] = "</EnamexOrgFin>"
        self.single_tags["EnamexOrgFin"] = "<EnamexOrgFin/>"

        # A finnish public office
        self.tags_start["Exc"] = "<Exc>"
        self.tags_end["Exc"] = "</Exc>"
        self.single_tags["Exc"] = "<Exc/>"

        # Events
        self.tags_start["Event"] = "<Event>"
        self.tags_end["Event"] = "</Event>"
        self.single_tags["Event"] = "<Event/>"

    def is_ner_start_tag(self, tag):
        values = list(self.tags_start.values())
        keys = list(self.tags_start.keys())

        return self.get_key(tag, values, keys)

    def is_ner_end_tag(self, tag):
        values = list(self.tags_end.values())
        keys = list(self.tags_end.keys())

        return self.get_key(tag, values, keys)

    def is_ner_single_tag(self, tag):
        values = list(self.single_tags.values())
        keys = list(self.single_tags.keys())

        return self.get_key(tag, values, keys)

    def get_key(self, tag, values, keys):

        if tag in values:
            i = values.index(tag)
            return keys[i]

        return None
