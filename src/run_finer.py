import subprocess
import fnmatch
import os
import ntpath
import logging, requests
import os.path
from pathlib import Path
import configparser

logger = logging.getLogger('Finer')
hdlr = logging.FileHandler('finer.log')
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.INFO)

class RunFiner:
    def __init__(self, directory, file_pattern, tool, input_texts):
        self.input_texts = list()
        if len(input_texts)>0:
            self.input_texts = input_texts

        self.folder = directory
        if not (self.folder.endswith("/")):
            self.folder += "/"

        self.file_extension = file_pattern
        self.output_files = list()
        self.output_texts = dict()
        self.pool_number = 4
        self.output_codes = dict()

        if len(tool) > 2:
            print(tool)
            self.tool = tool
        else:
            self.read_configs()

    def read_configs(self):

        config = configparser.ConfigParser()
        config.read('src/config.ini')

        self.tool = config['DEFAULT']['finer_url']
        self.pool_number = int(config['DEFAULT']['pool_number'])
        self.chunk_size = int(config['DEFAULT']['chunk_size'])

    def get_error_json(self, ind):
        data = {"ErrorCode": self.output_codes[ind][0], "ErrorReason": self.output_codes[ind][1], "ErrorMessage":self.output_texts[ind], "InputText":self.input_texts[ind]}
        return data

    def run(self):
        from itertools import zip_longest
        from multiprocessing import Process
        import multiprocessing

        texts = None
        files = None

        items = list(self.input_texts.items())
        if len(items) > 1:
            pool = multiprocessing.Pool(self.pool_number)
            chunksize = self.chunk_size
            chunks = [items[i:i + chunksize] for i in range(0, len(items), chunksize)]

            files, texts, codes = pool.map(self.execute_finer_parallel, chunks)
            pool.close()
            pool.join()
        else:
            print('items',items)
            self.execute_finer(items)

        if files != None:
            for f in files:
                self.output_files.extend(f)

        if texts != None:
            for i in texts:
                if i not in self.output_texts:
                    self.output_texts[i] = texts[i]
                    self.output_codes[i] = codes[i]
                else:
                    print("Text already in", self.output_texts[i], texts[i])

        return self.output_texts, self.output_codes

    def execute_finer_parallel(self, data):

        tmp_output_files = list()
        output_texts = dict()
        output_codes = dict()

        for tpl in data:
            ind =tpl[0]
            input_text = tpl[1]

            if len(input_text.split())> 1:
                output_file = str(self.folder)+"output/"+str(ind)+".txt"
                #print("IN=",input_text)
                #print("OUT=", output_file)
                tmp_output_files.append(output_file)
                my_file = Path(output_file)
                if not(my_file.exists()):

                    output, code, reason = self.summon_finer(input_text)  # +str(output_file)

                    #self.write_output(output, output_file)
                    output_texts[ind] = output
                    output_codes[ind] = (code, reason)
                else:
                    logging.info("File %s exists, moving on", output_file);
        return tmp_output_files, output_texts, output_codes



    def execute_finer(self, input):
        for ind in self.input_texts.keys():
            input_text = self.input_texts[ind]
            if len(input_text)> 1:
                output_file = str(self.folder)+"output/"+str(ind)+".txt"
                self.output_files.append(output_file)
                output, code, reason = self.summon_finer(input_text)
                self.output_texts[ind] = output
                self.output_codes[ind] = (code, reason)
                #self.write_output(output, output_file)
            else:
                print('Unable to split input', input_text)

    def summon_finer(self, input_text):
        output = ""
        status_code = 200
        reason = ""
        command = self.contruct_command(input_text)
        if self.tool.startswith('http'):
            print(self.tool)
            payload = {'text': str(input_text)}
            try:
                r = requests.get(self.tool, params=payload)

                print(r.text)
                status_code = r.status_code
                if status_code != 200:
                    reason = r.reason
                output = str(r.text)

                if "<title>500 Internal Server Error</title>" in output:
                    status_code = 500
                    reason = "Internal Server Error"
                #raise(requests.ConnectionError('test'))
            except requests.exceptions.Timeout as et:
                # Maybe set up for a retry, or continue in a retry loop
                print("Timeout:", et)
                status_code = et.response.status_code
                reason = et.response.reason
                output = str(et.response.text)
            except requests.exceptions.TooManyRedirects as etmr:
                # Tell the user their URL was bad and try a different one
                print("Too many redirects:", etmr)
                status_code = etmr.response.status_code
                reason = etmr.response.reason
                output = str(etmr.response.text)
            except requests.ConnectionError as errc:
                print("Error Connecting:", errc)
                status_code = 503
                reason = str(errc) #errc.message
                output = "" #errc.message
            except requests.exceptions.RequestException as e:
                # catastrophic error. bail.
                print("Request exception:", e.message)

                status_code = e.response.status_code
                reason = e.response.reason
                output = str(e.response.text)

        else:
            try:
                logging.info(command)
                output = subprocess.check_output(command, shell=True, executable='/bin/bash').decode("utf-8")
            except subprocess.CalledProcessError as cpe:
                logging.warning("Error: %s", cpe.output)
        return output, status_code, reason

    def contruct_command(self, input_text):
        if self.tool.startswith('http'):
            pass
        else:
            return self.tool+str(" <<< '")+str(input_text.replace("'","").replace("\\","")) +str("'")

    def write_output(self, output, file):
        f = open(file, 'w')
        f.write(output)
        f.close()

    def find_input_files(self):
        for file in os.listdir(self.folder):
            if fnmatch.fnmatch(file, self.file_extension):
                self.input_texts.append(self.folder + str(file))

    def get_output_files(self):
        return self.output_files

    def get_input_files(self):
        return self.input_texts

    def get_tool(self):
        return self.tool

    def set_tool(self, tool):
        self.tool = tool

    def set_input_files(self, input):
        self.input_texts = input

