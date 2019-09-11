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

            #    case: Oikeudenkäymiskaaren 31 luvun 17 §
            (r'(\b[a-zA-ZÄÖäö]+)( )?([1-9]{1}[0-9]{1,4})( )?(\b[a-zA-ZÄÖäö]+)( )?([1-9]{1}[0-9]{1,4})( )?(\§)?((\:[a-z]{1,4})( )?([1-9]?[0-9]{1,4})( )?(moment[a-zäöå]+))?',
            LawExtractor.__generateUris, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),

            #    case: Case Law refs (KKO/KHO 2004:19)
            (r'([A-Za-z]{3})([\:\ ]{1})([1-2]?[0-9]{1,4})([\:\ ]{1})([1-9]?[0-9]{1,4})',
            LawExtractor.__generateUris, [1, 2, 3, 4, 5])

            #    case: 2 luvun 1 §:n 2 momentissa
            #(r'([0-9]+)( )?((lu|moment|artikl)[a-zäö]+)?( )?([0-9]+)?( )?(\§([a-zäö\:]*)?)( )?([0-9]+)?( )?((lu|moment|artikl)[a-zäö]+)',
            # LawExtractor.__generateUris,
            # [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]),

            #    case: 5 tai 7 §:ssä
            #(r'([0-9]+)( )?(ja|tai)( )?([0-9]+)( )?((\§\:[a-zäö]+)|(artikl|moment|lu)[a-zäö]+)',
            # LawExtractor.__generateUris, [1, 2, 5, 3, 4, 5, 6, 7, 8, 9]),

            #    case: 7 luvun 3 §:n
            #(r'([0-9]+)( )?((\§\:[a-zäö]+)|(artikl|moment|lu)[a-zäö]+)',
            # LawExtractor.__generateUris, [1, 3, 4, 2, 3, 4]),


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