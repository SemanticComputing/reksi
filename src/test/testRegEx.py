import unittest
from src.RegEx import ExecuteRegEx, PatternFinder

class TestRegExRecognition(unittest.TestCase):

    def setUp(self):
        self.dates = {'0': 'Pääministeri muistutti, että vaikka hän itse oli henkilökohtaisesti EU:ssa pysymisen kannalla, kunnioittaa hän vuoden 2016 kansanäänestyksen tulosta.',
                      '1': 'Toukokuun 10. päivänä 2018 tapahtui kummia.',
                      '2': 'Helsingissä 5. maaliskuuta 2018 ei tapahtunut mitään.',
                      '3': 'Synnyin Lappeenrannassa 30.4.1986.',
                      '4': 'Syntymäpäiväni on 20.04.2019 ja siskoni syntymäpäivä on myös 20.04.2019.',
                      '5': 'Tavataan huomenna klo. 11:30 ruokalan edessä.',
                      #'6': 'Pitkäperjantai ja 2. pääsiäispäivä ovat aina arkipäiville sijoittuvia juhlapyhiä ja tarjoavat siten nelipäiväisen viikonlopun.',
                      #'7': 'Toukokuussa myös helatorstai antaa mahdollisuuden nelipäiväiseen viikonloppuun, jos ottaa perjantain 11. toukokuuta vapaaksi.',
                      #'8': 'Jos ottaa jouluna välipäivät (27.12. ja 28.12) sekä maanantaihin osuvan uudenvuodenaaton (31.12.) vapaaksi, voi nauttia peräti 11 päivän lomasta.'
                      }
        self.ssn = {'9': 'Sosiaaliturvatunnus 300486-123X kuuluu hänelle.'}
        self.www = {'10':'Kotimaisten kielten tutkimuskeskuksen Internet-osoite on http://www.kotus.fi.',
                    '11':'Tyypillisesti IP-osoitteita ei käytetä suoraan, vaan DNS-järjestelmä muuttaa selväkieliset osoitteet (kuten www.youtube.com) IP-osoitteiksi.',
                    '12':'Lisäesimerkkejä Internet-nimistä (eivät välttämättä nykyisin toimivia): http://santra.hut.fi, https://cc.tut.fi, www.chalmers.se, ftp://corn-flakes.ai.mit.edu.',
                    '13':'Muuan laajan tuntuinen suomenkielinen palvelu on Ketäon? osoitteessa "https://whois.tulevaisuus.net".'}
        self.ipv4s = {'14':'Tavallisesti IP-osoite esitetään neljän pisteellä erotetun luvun sarjana, esimerkiksi 145.97.39.155. IP-osoite ei yksilöi käyttäjää.',
                    '15': 'Esimerkki IP-numerosta: 130.233.224.50'}
        self.ipv6s = {'16': 'IPv6 osoite näyttää tältä 2001:0db8:0000:0000:0000:0000:1420:57ab.',
                      '17': 'Esimerkiksi 2001:0db8:85a3:08d3:1319:8a2e:0370:7334 on kelvollinen IPv6-osoite.'}
        self.emails = {'18': 'claire.tamper@aalto.fi',
                       '19': 'Sähköpostiosoitteeni on minna.tamper@gmail.com.',
                       '20': 'John.Doe@example.com on sähköpostiosoite.',
                       '21': 'Esimerkki oikeaoppisesta sähköpostiosoitteesta: simple@example.com.',
                       '22': 'Pisteet ja väliviivat ovat molemmat sallittuja sähköpostiosoitteessa: other.email-with-hyphen@example.com.',
                       '23': 'Myös plus merkit soveltuvat sähköpostiosoitteissa: user.name123.sorting@example.com.'}
        self.phone = {'24': '040 123 4567',
                      '25': '09 123 456',
                      '26': 'Puh. 03 1234 5678',
                      '27': '+358 9 123 4567',
                      '28': 'Puhelinnumeroni on +358 9 123 4567.',
                      '29': 'Hänet tavoittaa numerosta 0401234567.'}
        self.correct = {'0': ['2016'],
                        '1': ['Toukokuun 10. päivänä 2018'],
                        '2': ['5. maaliskuuta 2018'],
                        '3': ['30.4.1986'],
                        '4': ['20.04.2019'],
                        '5': ['huomenna','11:30'],
                        '6': ['Pitkäperjantai', '2. pääsiäispäivä'],
                        '7': ['Toukokuu', 'helatorstai', 'perjantai', '11. toukokuuta'],
                        '8': ['27.12', '28.12', 'maanantai', '31.12', '11 päivän'],
                        '9': ['300486-123X'],
                        '10': ['http://www.kotus.fi'],
                        '11': ['www.youtube.com'],
                        '12': ['http://santra.hut.fi', 'https://cc.tut.fi', 'www.chalmers.se', 'ftp://corn-flakes.ai.mit.edu'],
                        '13': ['https://whois.tulevaisuus.net'],
                        '14': ['145.97.39.155'],
                        '15': ['130.233.224.50'],
                        '16': ['2001:0db8:0000:0000:0000:0000:1420:57ab'],
                        '17': ['2001:0db8:85a3:08d3:1319:8a2e:0370:7334'],
                        '18': ['claire.tamper@aalto.fi'],
                        '19': ['minna.tamper@gmail.com'],
                        '20': ['John.Doe@example.com'],
                        '21': ['simple@example.com'],
                        '22': ['other.email-with-hyphen@example.com'],
                        '23': ['user.name123.sorting@example.com'],
                        '24': ['040 123 4567'],
                        '25': ['09 123 456'],
                        '26': ['03 1234 5678'],
                        '27': ['+358 9 123 4567'],
                        '28': ['+358 9 123 4567'],
                        '29': ['0401234567']}

        self.finder = PatternFinder()

    #def tearDown(self):
    #    self.finder.dispose()
    def parse_response(self, response):
        comp = list()
        for i,r in response.items():
            if r.get_name() not in comp:
                comp.append(r.get_name())

        return comp

    def test_social_security_number(self):
        for key, ssn in self.ssn.items():
            r = self.finder.identify_regex_patterns(ssn)
            res = [i.get_name() for i in r]
            print('RESULT:', res, self.correct[key], ssn)
            self.assertEqual(res, self.correct[key])

    def test_internet_addresses(self):
        for key, www in self.www.items():
            r = self.finder.identify_regex_patterns(www)
            res = [i.get_name() for i in r]
            print('RESULT:', res, self.correct[key], www)
            self.assertEqual(res, self.correct[key])

    def test_emails(self):
        for key, email in self.emails.items():
            r = self.finder.identify_regex_patterns(email)
            res = [i.get_name() for i in r]
            print('RESULT:', res, self.correct[key], email)
            self.assertEqual(res, self.correct[key])

    def test_dates(self):
        for key, date in self.dates.items():
            r = self.finder.identify_dates(date)
            res = self.parse_response(r)
            print('RESULT:', res, self.correct[key], date)
            self.assertEqual(res, self.correct[key])

    def test_ipv4s(self):
        for key, ip in self.ipv4s.items():
            r = self.finder.identify_regex_patterns(ip)
            res = [i.get_name() for i in r]
            print('RESULT:', res, self.correct[key], ip)
            self.assertEqual(res, self.correct[key])

    def test_ipv6s(self):
        for key, ip in self.ipv6s.items():
            r = self.finder.identify_regex_patterns(ip)
            res = [i.get_name() for i in r]
            print('RESULT:',res, self.correct[key], ip)
            self.assertEqual(res, self.correct[key])

    def test_phone_numbers(self):
        for key, pn in self.phone.items():
            r = self.finder.identify_regex_patterns(pn)
            res = [i.get_name() for i in r]
            print('RESULT:',res, self.correct[key], pn)
            self.assertEqual(res, self.correct[key])

if __name__ == '__main__':
    unittest.main()