'''
Created on 19.12.2016
# coding: utf-8
@author: petrileskinen
'''

import datetime
import re

class DateConverter(object):
    MONTHS= ['tammi','helmi','maalis','huhti', \
        'touko','kesä','heinä','elo', \
        'syys','loka','marras','joulu' ]
    MONTHGEX= '({})'.format('|'.join(MONTHS))
    
    SEASONS= ['kevä','kesä','syks','talv']
    SEASONGEX= '({})'.format('|'.join(SEASONS))
    
    ROMANS = [x.lower() for x in [ 'I', 'II', 'III', 'IV', 'V',
                 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII']]
    ROMANEX= '({})'.format('|'.join(ROMANS))
    
    MINTIME=datetime.date(1100,1,1)
    MAXTIME=datetime.date(2090,12,31)
    
    # OUTFORMAT="times:time_{}-{}"
    OUTFORMAT="{}-{}"
    
    DEFAULTCENTURY=1900
    @staticmethod
    def DEFAULTYEAR(yy):
        if yy<100:
            return yy+(DateConverter.__LAST if DateConverter.DEFAULTCENTURY=='auto' else DateConverter.DEFAULTCENTURY)
        else:
            return yy
    
    __LAST = None
    
    @staticmethod
    def find(txt):
        txt=' '+re.sub('<.+?>', '', txt)+' '
        
        arr=[]
        
        REGEXES = [
            #    case: 9.12.39-13.3.40
            (r'\D+((\d{1,2})\W+(\d{1,2})\W+(\d{2,4})[ .]*[–-][ .]*(\d{1,2})\W+(\d{1,2})\W+(\d{2,4}))',
            #    function call if regex matches:
             DateConverter.__generateDates,
            #     indices for function input, here [dd1,mm1,yy1,dd2,mm2,yy2] 
             [1,2,3, 4,5,6]),
            
            #    format in AcademySampo
            #    1.3.1795 - 12.1800
            (r'\D+((\d{1,2})\.(\d{1,2})\.(1[5-9]\d{2})\s*[-][ .]+(\d{1,2})\.(1[5-9]\d{2}))',
             DateConverter.__generateDates,
             [1,2,3, '31',4,5]),
            
            #    case: 15.3.1728-1733
            (r'\D+((\d{1,2})\W+(\d{1,2})\W+(\d{4})[ .]*[-][ .]*(\d{4}))',
             DateConverter.__generateDates,
             [1,2,3, '31','12',4]),
            
            
            #    case: 9.3-13.3.40, same year
            (r'\D+((\d{1,2})\W+(\d{1,2})[ .]*[-][ .]*(\d{1,2})\W+(\d{1,2})\W+(\d{2,4}))',
             DateConverter.__generateDates, [1,2,5, 3,4,5]),
            
            #    case: 9.-13.3.40, same month and year
            (r'\D+((\d{1,2})[ .]*[-][ .]*(\d{1,2})\W+(\d{1,2})\W+(\d{2,4}))',
             DateConverter.__generateDates, [1,3,4, 2,3,4]),
            
            #    case: 9.-13.III.40, same month and year
            (r'\D+((\d{1,2})[ .]*[-][ .]*(\d{1,2})\W+'+DateConverter.ROMANEX+'\W+(\d{2,4}))',
             DateConverter.__generateDates, [1,3,4, 2,3,4]),
            
            #    case: 13.3.40
            (r'\D+((\d{1,2})[ .]+(\d{1,2})\W+(\d{2,4}))',
             DateConverter.__generateDates, [1,2,3, 1,2,3]),
            
            #    case: 13.III.40
            (r'\D+((\d{1,2})\W+'+DateConverter.ROMANEX+'\W+(\d{2,4}))',
             DateConverter.__generateDates, [1,2,3, 1,2,3]),
                   
            #     case:    26. tammikuuta 1968 - 27. toukokuuta 1974
            (r'\D+((\d{1,2})[ .]*'+DateConverter.MONTHGEX+r'kuu[a-y]+[ .]*(\d{2,4})[ .]*[-][ .]*(\d{1,2})\D+'+DateConverter.MONTHGEX+r'ku[a-y]+[ .]*(\d{2,4}))',
             DateConverter.__generateDates, [1,2,3, 4,5,6]),
                   
            #     case:    26. tammikuuta - 27. toukokuuta 1974
            (r'\D+((\d{1,2})[ .]*'+DateConverter.MONTHGEX+r'kuu[a-y]+[ .]*[ .]*[-][ .]*(\d{1,2})\D+'+DateConverter.MONTHGEX+r'ku[a-y]+[ .]*(\d{2,4}))',
             DateConverter.__generateDates, [1,2,5, 3,4,5]),
                   
            #     case:    26. - 27. toukokuuta 1974
            (r'\D+((\d{1,2})[ .]*[-][ .]*(\d{1,2})[ .]*'+DateConverter.MONTHGEX+r'kuu[a-y]*\D*(\d{2,4}))',
             DateConverter.__generateDates, [1,3,4, 2,3,4]),
            
            #     case:    26. tammikuuta 1968
            (r'\D+((\d{1,2})[ .]*'+DateConverter.MONTHGEX+r'kuu[a-y]*\D*(\d{2,4}))',
             DateConverter.__generateDay, [1,2,3]),
            
            #    case: elokuun 15. 1940
            (r'('+DateConverter.MONTHGEX+r'kuu[a-y]*\s*(\d{1,2})\D+(\d{2,4}))',
             DateConverter.__generateDay, [2,1,3]),
            
            #    case: tammi-helmikuu 1940
            (r'('+DateConverter.MONTHGEX+r'\s*[-]\s*'+DateConverter.MONTHGEX+r'kuu[a-y]*\D*(\d{2,4}))',
             DateConverter.__generateMonths, [1,2,3]),
            
            #    case: elokuussa 1940
            (r'('+DateConverter.MONTHGEX+r'kuu[a-y]*\s*(\d{2,4}))',
             DateConverter.__generateMonth, [1,2]),
            
            #    case: keväällä 1940
            (r'('+DateConverter.SEASONGEX+r'[a-tv-zäö]{,6}\s*(\d{2,4}))',
             DateConverter.__generateSeason, [1,2]),
            
            #    case: 1900-luvun alkupuolella
            (r'\W*\D*((\d{1,2})00[-–]luvun al[ku][a-z]+)', 
             DateConverter.__generateCenturyFirstHalf, [1]), 
            
            #    case: 1900-luvun loppupuolella
            (r'\W*\D*((\d{1,2})00[-–]luvun lop[pu][a-z]+)', 
             DateConverter.__generateEndOfCentury, [1]), 
            
            #    case: 1900-luvulla
            (r'\W*\D*((\d{1,})00[-–]lu[vk]u[a-z]*)', 
             DateConverter.__generateCentury, [1]), 
                   
            #    case: 1930-luvun alkupuolella
            (r'\W*\D*((\d{2,4})0[-–]luvun al[ku][a-z]+)', 
             DateConverter.__generateDecadeFirstHalf, [1]), 
            
            #    case: 1930-luvun loppupuolella
            (r'\W*\D*((\d{2,4})0[-–]luvun lop[pu][a-z]+)', 
             DateConverter.__generateEndOfDecade, [1]), 
            
            #    case: 1930-luvulla
            (r'\W*\D*((\d{2,4})0[-–]lu[vk]u[a-z]*)', 
             DateConverter.__generateDecade, [1]), 
            
            #    case: 30-luvulla
            (r'\W*\D*((\d)0[-–]lu[vk]u[a-z]*)', 
             DateConverter.__generateDecade, [1]),
                   
            #    case: jouluaatto 1939
            (r'\W*((jouluaat[a-z]*)\s+(\d{2,4}))', 
             # Strings ('24','12') are constants, integers refer to parsed regex results:
             DateConverter.__generateDay, ['24','12', 2]), 
            
            #    TODO if needed, add itsenäisyysp., joulupäivä, tapaninp. etc,  accordingly
            
            #    case: joulu 1939
            (r'\W*((joulu[a-z]*)\s+(\d{2,4}))', 
             DateConverter.__generateDates, ['24','12', 2, '26','12', 2]),
            
            #    case: vappuna 1939
            (r'\W*((vap[pu][a-z]{6,})\s+(\d{2,4}))',
             DateConverter.__generateDates, ['30','4', 2, '1','5', 2]),
            
            #    TODO if needed, add pääsiäinen, vuodenvaihde etc,  accordingly
            #    easter:    https://en.wikipedia.org/wiki/Computus#Algorithms, 
            #               https://www.assa.org.au/edm#Calculator
            
            #    case: vuosina 1939-1945, 1939/1945
            (r'((\d{4})\s*[–/-]\s*(\d{4}))',
             DateConverter.__generateYears, [1,2]),
            
            #    case: vuosina 1699-00, 1699/00, TODO check, don't mix with 1689/5 may 1689
            (r'((\d{2}[6-9]\d)\s*[–/-]\s*([02-5]\d))',
             DateConverter.__generateYearSpanOverCentury, [1,2]),
            
            #    case: vuosina 1939-45, 1939/45
            (r'((\d{4})\s*[–/-]\s*(\d{2}))',
             DateConverter.__generateYearSpan, [1,2]),
            
            #    case: vuosina 39-45
            (r'((\d{2})\s*[–/-]\s*(\d{2}))',
             DateConverter.__generateYearSpan, [1,2]),
            
            #    case vsta 1934
            (r'vsta\s+((\d{2,4}))', 
             DateConverter.__generateAfterYear, [1]), 
            
            #    case: (1962-)
            (r'\(((\d\d+?)\s*[-––]\s*)\)', 
             DateConverter.__generateAfterYear, [1]), 
            
            #    case: 1934-
            (r'((\d\d+?)\s*[-–]\s+)', 
            DateConverter.__generateAfterYear, [1]), 
                   
            #    case: ennen 1934
            (r'(ennen\s*(\d{2,4}))',
             DateConverter.__generateBeforeYear, [1]), 
                   
            #    case: - 1934
            (r'([-–]\s*(\d{2,4}))',
             DateConverter.__generateBeforeYear, [1]), 
                   
            #    case: vuosi 1939
            (r'(\W(\d{3,4})\W)',
             DateConverter.__generateYear, [1])
        ]
        
        
        for (rgx, fnc, idx) in REGEXES:
            M=re.findall(rgx,txt,re.IGNORECASE)
            for m in M: 
                # As in ['24','12', 2], strings are constants,
                # integers refer to m[x] .e.g regex search results:
                a=[m[x] if type(x) is int else x for x in idx]
                # function call:
                try:
                    (date1,date2)= fnc(a)
                # Are dates appropriate:
                    if DateConverter.__qualify(date1,date2):
                        arr.append((date1,date2, m[0].strip()))
                        DateConverter.__updateLast(date1)
                        # remove found sequence from search string:
                        txt=txt.replace(m[0],' ')
                    elif DateConverter.__qualify(date2,date1):
                        arr.append((date2,date1, m[0].strip()))
                        DateConverter.__updateLast(date2)
                        # remove found sequence from search string:
                        txt=txt.replace(m[0],' ')
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
        st=[DateConverter.__toTimespan(m[0],m[1],m[2]) for m in arr]
        
        return st
    
    @staticmethod
    def __updateLast(d):
        if (DateConverter.DEFAULTCENTURY == 'auto') and d:
            DateConverter.__LAST = (d.year//100)*100
            #    print("__LAST set to {}".format(DateConverter.__LAST))
        
        
    @staticmethod
    def __generateDates(args): 
        # args: list in format: [day1,month1,year1,day2,month2,yy2]
        date1=None
        date2=None
        try:
            # convert to integers:
            # [dd,mm,yy,dd2,mm2,yy2]=[x for x in args[0:6]]
            dd=int(args[0])
            mm=args[1]
            yy=int(args[2])
            dd2=int(args[3])
            mm2=args[4]
            yy2=int(args[5])
            
            #if type(mm) is str:
            mm=mm.lower()
            if mm in DateConverter.MONTHS:
                mm=DateConverter.MONTHS.index(mm)+1
            elif mm in DateConverter.ROMANS:
                mm=DateConverter.ROMANS.index(mm)+1
            else:
                mm=int(mm)
            
            #if type(mm2) is str:
            mm2=mm2.lower()
            if mm2 in DateConverter.MONTHS:
                mm2=DateConverter.MONTHS.index(mm2)+1
            elif mm2 in DateConverter.ROMANS:
                mm2=DateConverter.ROMANS.index(mm2)+1
            else:
                mm2=int(mm2)
            
            yy = DateConverter.DEFAULTYEAR(yy)
            date1=DateConverter.__saveDate(yy,mm,dd)
            
            yy2 = DateConverter.DEFAULTYEAR(yy2)
            date2=DateConverter.__saveDate(yy2,mm2,dd2)
            
        except ValueError as e:
            print(e)
            pass
        
        return (date1,date2)
    
    @staticmethod
    def __generateDay(args):
        # args: list in format: [day,month,year]
        
        date1=None
        try:
            [dd,mm,yy]=args[0:3]
            if type(mm) is str:
                mm=mm.lower()
                if mm in DateConverter.MONTHS:
                    mm=DateConverter.MONTHS.index(mm)+1
                else:
                    mm=int(mm)
            yy=int(yy)
            
            yy = DateConverter.DEFAULTYEAR(yy)
            
            date1=datetime.date(yy,mm,int(dd))
            
        except ValueError as e:
            # print(e)
            pass
        
        return (date1,date1)
    
    @staticmethod
    def __generateMonths(args):
        return DateConverter.__entireTimespan([
            DateConverter.__generateMonth([args[0],args[2]]),
            DateConverter.__generateMonth([args[1],args[2]])
        ])
        
    @staticmethod
    def __generateMonth(args):
        date1=None
        date2=None
        try:
            [mm,yy]=args[0:2]
            mm=DateConverter.MONTHS.index(mm.lower())+1
            yy=int(yy)
            
            yy = DateConverter.DEFAULTYEAR(yy)
                
            date1=datetime.date(int(yy),mm,1)
            date2=DateConverter.__lastDayOfMonth(date1+datetime.timedelta(days=28))
        except Exception as e:
            # print(e)
            pass
        return (date1,date2)
    
    @staticmethod
    def __generateSeason(args):
        # NB: "Winter 1940" is interpreted as 1st Dec 1939--28th Feb 1940 
        date1=None
        date2=None
        try:
            [ss,yy]=args[0:2]
            # last month of season [0] kevat -> toukokuu
            i=DateConverter.SEASONS.index(ss.lower())
            mm=1+((4+3*i)%12)
            
            yy = DateConverter.DEFAULTYEAR(int(yy))
            
            date2=DateConverter.__lastDayOfMonth(datetime.date(yy,mm,1)+datetime.timedelta(days=28))
            date1=DateConverter.__lastDayOfMonth(date2+datetime.timedelta(days=-93))+datetime.timedelta(days=1)
            
        except Exception as e:
            # print(e)
            pass
        return (date1,date2)
    
    @staticmethod
    def __generateCentury(args):
        return DateConverter.__entireTimespan([
            DateConverter.__generateYear([args[0]+'00']),
            DateConverter.__generateYear([args[0]+'99'])
        ])

    
    @staticmethod
    def __generateCenturyFirstHalf(args):
        return DateConverter.__entireTimespan([
            DateConverter.__generateYear([args[0]+'00']),
            DateConverter.__generateYear([args[0]+'49'])
        ])
    
    @staticmethod
    def __generateEndOfCentury(args):
        return DateConverter.__entireTimespan([
            DateConverter.__generateYear([args[0]+'50']),
            DateConverter.__generateYear([args[0]+'99'])
        ])

        
    @staticmethod
    def __generateDecade(args):
        return DateConverter.__entireTimespan([
            DateConverter.__generateYear([args[0]+'0']),
            DateConverter.__generateYear([args[0]+'9'])
        ])
    
    @staticmethod
    def __generateDecadeFirstHalf(args):
        return DateConverter.__entireTimespan([
            DateConverter.__generateYear([args[0]+'0']),
            DateConverter.__generateYear([args[0]+'4'])
        ])
    
    @staticmethod
    def __generateEndOfDecade(args):
        return DateConverter.__entireTimespan([
            DateConverter.__generateYear([args[0]+'5']),
            DateConverter.__generateYear([args[0]+'9'])
        ])
    
    @staticmethod
    def __generateYears(args):
        return DateConverter.__entireTimespan([
            DateConverter.__generateYear([args[0]]),
            DateConverter.__generateYear([args[1]])
        ])
    
    @staticmethod
    def __generateYearSpan(args):
        #    1939-45 tai 39-45
        y1 = args[0]
        y2 = (y1[:2] if len(y1)>2 else "")+args[1]
        
        return DateConverter.__entireTimespan([
            DateConverter.__generateYear([y1]),
            DateConverter.__generateYear([y2])
        ])
    
    @staticmethod
    def __generateYearSpanOverCentury(args):
        #    1699-00, 1699/00
        y1 = args[0]
        cn = int(y1[:2]) + 1
        y2 = str(cn) + args[1]# (y1[:2] if len(y1)>2 else "")+args[1]
        
        return DateConverter.__entireTimespan([
            DateConverter.__generateYear([y1]),
            DateConverter.__generateYear([y2])
        ])

    @staticmethod
    def __generateYear(args):
        date1=None
        date2=None
        try:
            yy=args[0]
            yy = DateConverter.DEFAULTYEAR(int(yy))
                
            date1=datetime.date(yy,1,1)
            date2=datetime.date(yy,12,31)
            
        except Exception as e:
            # print(e)
            pass
        return (date1,date2)
    
    @staticmethod
    def __generateAfterYear(args):
        date1=None
        date2=None
        try:
            yy=args[0]
            yy = DateConverter.DEFAULTYEAR(int(yy))
            date1=datetime.date(yy,1,1)
            
        except Exception as e:
            # print(e)
            pass
        return (date1,date2)
    
    @staticmethod
    def __generateBeforeYear(args):
        date1=None
        date2=None
        try:
            yy=args[0]
            yy = DateConverter.DEFAULTYEAR(int(yy))
            date2=datetime.date(yy,1,1)
            
        except Exception as e:
            # print(e)
            pass
        return (date1,date2)
    
    '''
    @staticmethod
    def __generateXmass(args):
        return DateConverter.__generateDates([24,12,args[0],26,12,args[0]])
    
    @staticmethod
    def __generateMayday(args):
        return DateConverter.__generateDates([30,4,args[0],1,5,args[0]])
    '''
    
    @staticmethod
    def __qualify(date1,date2):
        if date2==None: date2=date1
        if date1==None: date1=date2
        return date1!=None and date2!=None and \
            date1<=date2 and \
            DateConverter.MINTIME<=date1 and \
            date2 <= DateConverter.MAXTIME
    
    
    @staticmethod
    def __toTimespan(date1,date2, txt=None):
        if isinstance(DateConverter.OUTFORMAT, list):
            return [date1, date2, txt]
        return DateConverter.OUTFORMAT.format(date1,date2, txt)
    
    @staticmethod
    def __saveDate(yy,mm,dd):
        dt=None
        try:
            dt=datetime.date(yy,mm,dd)
        except ValueError as e:
            if str(e)=='day is out of range for month' and dd<32:
                # print('Virhe kuukauden päivässä {}-{}-{}'.format(yy,mm,dd))
                dt=DateConverter.__lastDayOfMonth(datetime.date(yy,mm,27))
                # print('Erroneous date {}-{}-{} replaced with: {}'.format(yy,mm,dd,dt))
            else:
                print('{}:\t{}-{}-{}'.format(e,yy,mm,dd))
        return dt
    
    @staticmethod
    def __lastDayOfMonth(date2):
        date2 = datetime.date(date2.year, date2.month, 28)
        while True:
            if date2.day==1:
                date2 += datetime.timedelta(days=-1)
                break
            else:
                date2 += datetime.timedelta(days=1)
        return date2
    
    @staticmethod
    def __entireTimespan(arr):
        # choose earliest and latest date
        # from a list of datetime.dates:
        return (min([x[0] for x in arr]),
                max([x[-1] for x in arr]))
    
    @staticmethod
    def makeUrl(d1, d2):
        if not d1:
            return "-"+str(d2)
        if not d2:
            return str(d1)+"-"
        
        st=str(d1)+"-"+str(d2)
        
        #    entire year
        #    1968
        st = re.sub(r"(\d{4})-01-01-\1-12-31", "\g<1>", st)
        
        #    year span
        #    1950-52
        st = re.sub(r"(\d{2})(\d{2})-01-01-\1(\d{2})-12-31", "\g<1>\g<2>-\g<3>", st)
        #    1999-2000
        st = re.sub(r"(\d{4})-01-01-(\d{4})-12-31", "\g<1>-\g<2>", st)
        
        # month
        st = re.sub(r"(\d{4})-(0[13578]|1[02])-01-\1-\2-31", "\g<1>-\g<2>", st)
        st = re.sub(r"(\d{4})-(0[469]|11)-01-\1-\2-30", "\g<1>-\g<2>", st)
        st = re.sub(r"(\d{4})-(02)-01-\1-\2-(2[89])", "\g<1>-\g<2>", st)
        
        #    single day "1968-01-26-1968-01-26"
        st = re.sub(r"(.{10})-\1", "\g<1>", st)
        return st

    """
    Extends days to months, months to year, year to decades, and decades to centuries
    """
    @staticmethod
    def broaderTimespan(d1, d2):
        if not (d1 and d2):
            return None, None, None
        
        if isinstance(d1, str):
            d1 = datetime.datetime.strptime(d1, '%Y-%m-%d').date()
        if isinstance(d2, str):
            d2 = datetime.datetime.strptime(d2, '%Y-%m-%d').date()
        
        b1, b2, label = None, None, None
        if d1.year == d2.year:
            if d1.month == d2.month:
                # two days of a month
                b1 = datetime.date(d1.year,d1.month,1)
                b2 = DateConverter.__lastDayOfMonth(d1)
                
                if b1==d1 and b2==d2:
                    #   first and last of month -> return year
                    return datetime.date(d1.year,1,1), datetime.date(d1.year,12,31), str(d1.year)
                else:
                    #   days within a month
                    label = "{}kuu {}".format(DateConverter.MONTHS[d1.month-1], d1.year)
                    return b1, b2, label
            
            if d1.day != 1 or d2.day != 31 or d1.month != 1 or d2.month != 12 :
                return datetime.date(d1.year,1,1), datetime.date(d1.year,12,31), str(d1.year)
        
        # decade
        if d1.year//10 == d2.year//10:
            # first day of decade
            b1 = datetime.date((d1.year//10)*10,1,1)
            # last day of decade
            b2 = datetime.date((d2.year//10)*10+9,12,31)
            
            #   if not entire decade
            if b1!=d1 or b2!=d2:
                return b1, b2, "{}-{}".format(b1.year, b2.year) 
        
        # 50 years
        if d1.year//50 == d2.year//50:
            # first day of half century
            b1 = datetime.date((d1.year//50)*50,1,1)
            # last day of half century
            b2 = datetime.date((d2.year//50)*50+49,12,31)
            
            #   if not entire half century
            if b1!=d1 or b2!=d2:
                return b1, b2, "{}-{}".format(b1.year, b2.year) 

        # century
        if d1.year//100 == d2.year//100:
            b1 = datetime.date((d1.year//100)*100,1,1)
            b2 = datetime.date((d2.year//100)*100+99,12,31)
            
            if b1!=d1 or b2!=d2:
                    return b1, b2, "{}-{}".format(b1.year, b2.year) 
        
        return None, None, None
    
    @staticmethod
    def find_first(st):
        res = DateConverter.find(st)
        if len(res):
            res.sort(key=lambda x: st.index(x[-1]) if x[-1] in st else 1000)
            return res[0]
        return None

    @staticmethod
    def find_last(st):
        res = DateConverter.find(st)
        if len(res):
            res.sort(key=lambda x: st.index(x[-1]) if x[-1] in st else 1000)
            return res[-1]
        return None
    
"""
st = "noin 1726. Talollisen poika Pornaisista. Porvoon lukion oppilas 2.10.1746 - 1.1751."
st2 = "noin Talollisen poika Pornaisista oppilas"
DateConverter.OUTFORMAT = []
print(DateConverter.find_first(st))
"""

"""
for d1, d2 in [("1968-01-26","1968-01-26"), ("1968-01-01","1968-01-31")]:
    print(d1,d2)
    b1, b2, label = DateConverter.broaderTimespan(d1, d2)
    
    while b1 and b2:
        print(b1,b2, label)
        b1, b2, label = DateConverter.broaderTimespan(b1, b2)
"""

def mainTest():
    DateConverter.OUTFORMAT=[]
    EARLIEST = datetime.date(1550, 1, 1)
    LATEST = datetime.date(1950, 1, 1)
    DateConverter.MINTIME = EARLIEST
    DateConverter.MAXTIME = LATEST
    for st in ['9.3-13.3.1940',
               '9.3-13.3.40',
               "9.1-29.2.40",
               "20.-28.2.39",
               "9.1-29.2 41",
               "26.-27.2.40",
               "26.1 1968",
               "4.1.1940",
               "26. kesäkuuta 1968",
               "126. Kesäkuuta 1968",
               "huhtikuun 31., 1968",
               "helmikuun 29:sta 1939",
               "26. helmikuuta 1940 oli ennen 1. maaliskuuta 1940",
               "helmikuuhun 1972",
               "Helmikuusta 1974",
               "Tammikuusta 1968 toukokuuhun 1974" ,
               "Vuonna 1943",
               "Kevät 1928",
               "Kesällä 1974",
               "Kesäkuu 1974",
               "Syksystä 1974",
               
               "Talvella 2016",
               "Jouluna 2016",
               "jouluaatoksi 2016",
               "joulukuussa 2016",
               "syys-joulukuu 2016",
               
               "Vappuna 1942",
               "tammi-marraskuu 1968",
               "marraskuu 1939 - maaliskuu 1940",
               "1968-74, 1980",
               "Vuosina 1939-1945",
               "6. helmikuuta 1943 - 17. helmikuuta 1944",
               "kapteeniluutnantti Pentti Ahola. Kesäkuu 1944 - kevät 1945",
               "Everstiluutnantti Ludvig Mäntylä 27.11.1943-3.11.1944",
               "eversti Claes Winell (31. joulukuuta 1941 kenraalimajuri) 10. kesäkuuta 1941 - 9. tammikuuta 1943",
               "ratsumestari Lars Rönnquist 18. kesäkuuta 1941 - 13. marraskuuta 1941 ja 21. maaliskuuta 1942 - 31. heinäkuuta 1942 ollen väliajan sairaana",
               "kapteeni Yrjö Patomäki 9.-12. kesäkuuta 1944 (sijainen)",
               "26. tammikuuta - 27. toukokuuta 1974",
               "K pienenä",
               "Rehn oli tuolloin aktiivinen nuori keskustaliikkeessä ja kuului ryhmään, jossa vaikuttivat esimerkiksi Maria Kaisa Aula (1962–) ja Anu Vehviläinen (1963–)",
               "Tilan sähkönkulutus oli ollut vuonna 1983 19.905 kilowattituntia ja vuonna 1984 24.523 kilowattituntia."
               "Lisäksi Aarno Antero Tarkkio on vaatinut yhtiön velvoittamista suorittamaan hänelle takaisin 31.1.1983 jälkeiseltä ajalta liikaa perittyjä sähkömaksuja 4.768,43 markkaa 16 prosentin korkoineen haasteen tiedoksiantopäivästä lukien sekä korvaamaan hänen oikeudenkäyntikulunsa.",
               "Mikäli sähkövirran käyttö ylitti 5.000 kilowattitunnin vuotuismäärän, perittiin yli menevältä osalta maksu samojen perusteiden mukaan kuin tilapäisiltä sähkövirran kuluttajilta.",
               "4.000.000.000 euroa",
                "4.000.000.000,00 markan",
                "2000 dollaria",
                "5€",
                "5,55€",
                "... euroa",
                "1...4 euroa",
                "1.1.1.1 euroa",
                "55 000 dollaria",
                "Toimikauden alussa 90-luvun laman ...",
                "tuettuna 1999 - 2007 henkiset ajan ilmaukset",
                "tuettuna 1999-2007 henkiset ajan ilmaukset",
                "Maanmittari Oulun läänissä 1800-19",
                "Kokemäen maamieskoulun joht. 1818-19. ",
                "Kokemäen maamieskoulun joht. 1800-15.",
                "Kokemäen maamieskoulun joht. 1810-1818.",
                "Kesälahdella 1790",
                "Viipurin hovioik. asessori 1904-06 ja 08-09",
               "Viipurin lääninsairaalan alilääkäri 1897-1904, esikaupunkien piirilääkäri 1904-23, yksityislääkäri Viipurissa 23-32",
               "Pohjalaisen osakunnan kuraattori, sitten inspehtori 1723-26.",
               "Viinuri Tukholmassa 1699, samalla hovisoittokunnan musikantti 1702-29",
               "Valtiopäivämies 1693, 1710 ja 1713-14",
               "Örebron koulun oppilas 1623 - 1626."
               ]:
        
        DateConverter.DEFAULTCENTURY='auto'
        st2=DateConverter.find(st)
        
        if st2:
            print('{}\t{}'.format(st2,st))
            for d0,d1, _ in st2:
                print(DateConverter.makeUrl(d0,d1))
        else:
            print('Could not analyze: "{}"'.format(st))
    return

if __name__ == '__main__':
    mainTest()

    


