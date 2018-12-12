import logging

logger = logging.getLogger('NamedEntity')
hdlr = logging.FileHandler('namedentity.log')
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.INFO)

class NeScore:
    def __init__(self):
        self.longest = 0 # longest entity is the best entity
        self.ne_type = 0 # importance of types of entities
        self.method = 0 # reliability of the method used for extraction of entity from text
        self.link = 0 # has been linked to some ontology
        self.ne_priority = {"PersonName": 8, "PlaceName": 5, "OrganizationName": 6, "ExpressionTime": 7,
                            "AddressName": 2, "PoliticalLocation": 4, "GeographicalLocation": 3,
                            "EducationalOrganization": 5, "VocationName":4, "AnonymEntity": 1,
                            "CorporationsName":6, "SportsOrganizations":6,
                            "CultureOrganization":6, "PoliticalOrganization":6,
                            "MediaOrganization":6, "Title":4, "FinnishOrganization":6,
                               "Executive":5, "Event":5 }

    def total_score(self):
        s = self.longest + self.link + self.method + self.ne_type
        return int(s)

    def set_longest(self, score):
        self.longest = score

    def set_ne_type(self, score):
        self.ne_type = score

    def set_link(self, score):
        self.link = score

    def set_method(self, score):
        self.method = score

    def set_type_score(self, type):
        self.ne_type = self.ne_priority[type]

    def __repr__(self):
        return self.total_score()

    def __str__(self):
        return str(self.total_score())

