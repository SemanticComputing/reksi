# Regular Expression Service

Annotates given text with whatever user wants to search from text using regular expressions (regex). The regexes can be specified in the settings file where the type of entities is given in [ BRACKETS ] and the regex is given for the pattern variable. The date identification is done separately for Finnish language texts as part of the application. Currently this cannot be turned off.

## Getting Started

To execute, set environment variable
```
export FLASK_APP=src/run.py
```

Then run ``` flask run ```

### Prerequisites

Uses Python 3.5 or newer
Python libraries: flask, dateparser, nltk

## Usage

Can be used using POST or GET.

For GET
```
http://127.0.0.1:5000/?text=P%C3%A4%C3%A4ministeri%20muistutti,%20ett%C3%A4%20vaikka%20h%C3%A4n%20itse%20oli%20henkil%C3%B6kohtaisesti%20EU:ssa%20pysymisen%20kannalla,%20kunnioittaa%20h%C3%A4n%20vuoden%202016%20kansan%C3%A4%C3%A4nestyksen%20tulosta.
```
For POST
```
curl -H "Content-type: text/plain" \
-X POST http://127.0.0.1:5000/ --data-binary "Pääministeri muistutti, että vaikka hän itse oli henkilökohtaisesti EU:ssa pysymisen kannalla, kunnioittaa hän vuoden 2016 kansanäänestyksen tulosta."
```

### Configurations

The configurations for the service can be found in the ```src/config.ini```.

### Output

Example output:

```
{"data": "[{'text': 'Pääministeri muistutti, että vaikka hän itse oli henkilökohtaisesti EU:ssa pysymisen kannalla, kunnioittaa hän vuoden 2016 kansanäänestyksen tulosta.', 'id': 0, 'results': [{'end_index': 122, 'start_index': 118, 'entity': '2016', 'type': 'DATETIME'}]}]", "status": 200}
```

The api returns a json response that contains the status_code where 200 is a success and -1 represents error. In both cases the data is contained in the data field. In case of errors the error message, code, reason are in their own fields. In case of successful execution, the data contains the resultset. In the resultset the sentences are indexed from 0 to n and each sentence has its named entities, string form of each sentence, index in sentence (nth characters), type and the string.

### Running in Docker

`./docker-build.sh`: builds Regular Expression Service

`./docker-run.sh`: runs the service
