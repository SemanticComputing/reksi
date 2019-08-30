import re


class LawExtractor(object):

    @staticmethod
    def find(txt):
        txt = ' ' + re.sub('<.+?>', '', txt) + ' '

        arr = []

        REGEXES = [
            #    case: hallintolaki (434/2003)
            (r'(\b[a-zA-ZÄÖäö]+)( )?\((([0-9]{1,4})\/([0-9]{1,4}))\)',
             #    function call if regex matches:
             LawExtractor.__generateUris,
             #     indices for function input, here [dd1,mm1,yy1,dd2,mm2,yy2] 
             [1, 2, 3, 4, 5]),

            #    case: 2 luvun 1 §:n 2 momentissa
            (r'([0-9]+)( )?((lu|moment|artikl)[a-zäö]+)?( )?([0-9]+)?( )?(\§([a-zäö\:]*)?)( )?([0-9]+)?( )?((lu|moment|artikl)[a-zäö]+)',
             LawExtractor.__generateUris,
             [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]),

            #    case: 5 tai 7 §:ssä
            (r'([0-9]+)( )?(ja|tai)( )?([0-9]+)( )?((\§\:[a-zäö]+)|(artikl|moment|lu)[a-zäö]+)',
             LawExtractor.__generateUris, [1, 2, 5, 3, 4, 5, 6, 7, 8, 9]),

            #    case: 7 luvun 3 §:n
            (r'([0-9]+)( )?((\§\:[a-zäö]+)|(artikl|moment|lu)[a-zäö]+)',
             LawExtractor.__generateUris, [1, 3, 4, 2, 3, 4]),

            #    case: 9.-13.III.40, same month and year
            (r'\D+((\d{1,2})[ .]*[-][ .]*(\d{1,2})\W+' + LawExtractor.ROMANEX + '\W+(\d{2,4}))',
             LawExtractor.__generateUris, [1, 3, 4, 2, 3, 4]),

            #    case: 13.3.40
            (r'\D+((\d{1,2})[ .]+(\d{1,2})\W+(\d{2,4}))',
             LawExtractor.__generateUris, [1, 2, 3, 1, 2, 3]),

            #    case: 13.III.40
            (r'\D+((\d{1,2})\W+' + LawExtractor.ROMANEX + '\W+(\d{2,4}))',
             LawExtractor.__generateUris, [1, 2, 3, 1, 2, 3]),

            #     case:    26. tammikuuta 1968 - 27. toukokuuta 1974
            (
            r'\D+((\d{1,2})[ .]*' + LawExtractor.MONTHGEX + r'kuu[a-y]+[ .]*(\d{2,4})[ .]*[-][ .]*(\d{1,2})\D+' + LawExtractor.MONTHGEX + r'ku[a-y]+[ .]*(\d{2,4}))',
            LawExtractor.__generateUris, [1, 2, 3, 4, 5, 6]),

            #     case:    26. tammikuuta - 27. toukokuuta 1974
            (
            r'\D+((\d{1,2})[ .]*' + LawExtractor.MONTHGEX + r'kuu[a-y]+[ .]*[ .]*[-][ .]*(\d{1,2})\D+' + LawExtractor.MONTHGEX + r'ku[a-y]+[ .]*(\d{2,4}))',
            LawExtractor.__generateUris, [1, 2, 5, 3, 4, 5]),

            #     case:    26. - 27. toukokuuta 1974
            (r'\D+((\d{1,2})[ .]*[-][ .]*(\d{1,2})[ .]*' + LawExtractor.MONTHGEX + r'kuu[a-y]+\D*(\d{2,4}))',
             LawExtractor.__generateUris, [1, 3, 4, 2, 3, 4]),

            #     case:    26. tammikuuta 1968
            (r'\D+((\d{1,2})[ .]*' + LawExtractor.MONTHGEX + r'kuu[a-y]+\D*(\d{2,4}))',
             LawExtractor.__generateDay, [1, 2, 3]),

            #    case: elokuun 15. 1940
            (r'(' + LawExtractor.MONTHGEX + r'kuu[a-y]+\s*(\d{1,2})\D+(\d{2,4}))',
             LawExtractor.__generateDay, [2, 1, 3]),

            #    case: tammi-helmikuu 1940
            (r'(' + LawExtractor.MONTHGEX + r'\s*[-]\s*' + LawExtractor.MONTHGEX + r'kuu[a-y]+\D*(\d{2,4}))',
             LawExtractor.__generateMonths, [1, 2, 3]),

            #    case: elokuussa 1940
            (r'(' + LawExtractor.MONTHGEX + r'kuu[a-y]+\s*(\d{2,4}))',
             LawExtractor.__generateMonth, [1, 2]),

            #    case: keväällä 1940
            (r'(' + LawExtractor.SEASONGEX + r'[a-tv-z]+\s*(\d{2,4}))',
             LawExtractor.__generateSeason, [1, 2]),

            #    case: 1900-luvun alkupuolella
            (r'\W*\D*((\d{1,2})00[-–]luvun al[ku][a-z]+)',
             LawExtractor.__generateCenturyFirstHalf, [1]),

            #    case: 1900-luvun loppupuolella
            (r'\W*\D*((\d{1,2})00[-–]luvun lop[pu][a-z]+)',
             LawExtractor.__generateEndOfCentury, [1]),

            #    case: 1900-luvulla
            (r'\W*\D*((\d{1,})00[-–]lu[vk]u[a-z]*)',
             LawExtractor.__generateCentury, [1]),

            #    case: 1930-luvun alkupuolella
            (r'\W*\D*((\d{2,4})0[-–]luvun al[ku][a-z]+)',
             LawExtractor.__generateDecadeFirstHalf, [1]),

            #    case: 1930-luvun loppupuolella
            (r'\W*\D*((\d{2,4})0[-–]luvun lop[pu][a-z]+)',
             LawExtractor.__generateEndOfDecade, [1]),

            #    case: 1930-luvulla
            (r'\W*\D*((\d{2,4})0[-–]lu[vk]u[a-z]*)',
             LawExtractor.__generateDecade, [1]),

            #    case: jouluaatto 1939
            (r'\W*((jouluaat[a-z]*)\s+(\d{2,4}))',
             # Strings ('24','12') are constants, integers refer to parsed regex results:
             LawExtractor.__generateDay, ['24', '12', 2]),

            #    TODO if needed, add itsenäisyysp., joulupäivä, tapaninp. etc,  accordingly

            #    case: joulu 1939
            (r'\W*((joulu[a-z]*)\s+(\d{2,4}))',
             LawExtractor.__generateUris, ['24', '12', 2, '26', '12', 2]),

            #    case: vappuna 1939
            (r'\W*((vap[pu][a-z]{6,})\s+(\d{2,4}))',
             LawExtractor.__generateUris, ['30', '4', 2, '1', '5', 2]),

            #    TODO if needed, add pääsiäinen, vuodenvaihde etc,  accordingly
            #    easter:    https://en.wikipedia.org/wiki/Computus#Algorithms, 
            #               https://www.assa.org.au/edm#Calculator

            #    case: vuosina 1939-45
            (r'((\d{4})\s*[–/-]\s*(\d{2,4}))',
             LawExtractor.__generateYears, [1, 2]),

            #    case vsta 1934
            (r'vsta\s+((\d{2,4}))',
             LawExtractor.__generateAfterYear, [1]),

            #    case: (1962-)
            (r'\(((\d\d+?)\s*[-––]\s*)\)',
             LawExtractor.__generateAfterYear, [1]),

            #    case: 1934-
            (r'((\d\d+?)\s*[-–]\s+)',
             LawExtractor.__generateAfterYear, [1]),

            #    case: ennen 1934
            (r'(ennen\s*(\d{2,4}))',
             LawExtractor.__generateBeforeYear, [1]),

            #    case: - 1934
            (r'([-–]\s*(\d{2,4}))',
             LawExtractor.__generateBeforeYear, [1]),

            #    case: vuosi 1939
            (r'(\W(\d{3,4})\W)',
             LawExtractor.__generateYear, [1])
        ]

        for (rgx, fnc, idx) in REGEXES:
            M = re.findall(rgx, txt, re.IGNORECASE)
            for m in M:
                # As in ['24','12', 2], strings are constants,
                # integers refer to m[x] .e.g regex search results:
                a = [m[x] if type(x) is int else x for x in idx]
                # function call:
                try:
                    (date1, date2) = fnc(a)
                    # print("Did not fail:",txt, " with ", rgx)
                    # Are dates appropriate:
                    if LawExtractor.__qualify(date1, date2):
                        arr.append((date1, date2, m[0].strip()))
                        # remove found sequence from search string:
                        txt = txt.replace(m[0], ' ')
                    elif LawExtractor.__qualify(date2, date1):
                        arr.append((date2, date1, m[0].strip()))
                        # remove found sequence from search string:
                        txt = txt.replace(m[0], ' ')
                    else:
                        print("Doesn't qualify as date?", date1, date2)
                except TypeError:
                    print("TypeError {}".format(txt))

                else:
                    # print('Unresolved: {}'.format(m[0]))
                    pass
        else:
            # exit loop after first satisfying result is found:
            # if len(arr): break
            # print('Unresolved: {}'.format(txt))
            pass
        # format output:
        st = [LawExtractor.__toTimespan(m[0], m[1], m[2]) for m in arr]

        return st

    @staticmethod
    def __generateUris(args):
        # args: list in format: [day1,month1,year1,day2,month2,yy2]
        date1 = None
        date2 = None
        try:
            # convert to integers:
            # [dd,mm,yy,dd2,mm2,yy2]=[x for x in args[0:6]]
            dd = int(args[0])
            mm = args[1]
            yy = int(args[2])
            dd2 = int(args[3])
            mm2 = args[4]
            yy2 = int(args[5])

            # if type(mm) is str:
            mm = mm.lower()
            if mm in DateConverter.MONTHS:
                mm = DateConverter.MONTHS.index(mm) + 1
            elif mm in DateConverter.ROMANS:
                mm = DateConverter.ROMANS.index(mm) + 1
            else:
                mm = int(mm)

            # if type(mm2) is str:
            mm2 = mm2.lower()
            if mm2 in DateConverter.MONTHS:
                mm2 = DateConverter.MONTHS.index(mm2) + 1
            elif mm2 in DateConverter.ROMANS:
                mm2 = DateConverter.ROMANS.index(mm2) + 1
            else:
                mm2 = int(mm2)

            yy = DateConverter.DEFAULTYEAR(yy)
            date1 = DateConverter.__saveDate(yy, mm, dd)

            yy2 = DateConverter.DEFAULTYEAR(yy2)
            date2 = DateConverter.__saveDate(yy2, mm2, dd2)

        except ValueError as e:
            print(e)
            pass

        return (date1, date2)