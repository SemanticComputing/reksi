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
    
    MINTIME=datetime.date(1700,1,1)
    MAXTIME=datetime.date(2020,12,31)
    
    # OUTFORMAT="times:time_{}-{}"
    OUTFORMAT="{}-{}"
    
    DEFAULTCENTURY=1900
    @staticmethod
    def DEFAULTYEAR(yy):
        if yy<100:
            return yy+DateConverter.DEFAULTCENTURY
        else:
            return yy
    
    
    @staticmethod
    def find(txt):
        txt=' '+re.sub('<.+?>', '', txt)+' '
        
        arr=[]
        
        REGEXES = [
            #    case: 9.12.39-13.3.40
            (r'\D+((\d{1,2})\W+(\d{1,2})\W+(\d{2,4})[ .]*[-][ .]*(\d{1,2})\W+(\d{1,2})\W+(\d{2,4}))',
            #    function call if regex matches:
             DateConverter.__generateDates,
            #     indices for function input, here [dd1,mm1,yy1,dd2,mm2,yy2] 
             [1,2,3, 4,5,6]),
            
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
            (r'\D+((\d{1,2})[ .]*[-][ .]*(\d{1,2})[ .]*'+DateConverter.MONTHGEX+r'kuu[a-y]+\D*(\d{2,4}))',
             DateConverter.__generateDates, [1,3,4, 2,3,4]),
            
            #     case:    26. tammikuuta 1968
            (r'\D+((\d{1,2})[ .]*'+DateConverter.MONTHGEX+r'kuu[a-y]+\D*(\d{2,4}))',
             DateConverter.__generateDay, [1,2,3]),
            
            #    case: elokuun 15. 1940
            (r'('+DateConverter.MONTHGEX+r'kuu[a-y]+\s*(\d{1,2})\D+(\d{2,4}))',
             DateConverter.__generateDay, [2,1,3]),
            
            #    case: tammi-helmikuu 1940
            (r'('+DateConverter.MONTHGEX+r'\s*[-]\s*'+DateConverter.MONTHGEX+r'kuu[a-y]+\D*(\d{2,4}))',
             DateConverter.__generateMonths, [1,2,3]),
            
            #    case: elokuussa 1940
            (r'('+DateConverter.MONTHGEX+r'kuu[a-y]+\s*(\d{2,4}))',
             DateConverter.__generateMonth, [1,2]),
            
            #    case: keväällä 1940
            (r'('+DateConverter.SEASONGEX+r'[a-tv-z]+\s*(\d{2,4}))',
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
            
            #    case: vuosina 1939-45
            (r'((\d{4})\s*[–/-]\s*(\d{2,4}))',
             DateConverter.__generateYears, [1,2]),
            
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
                    #print("Did not fail:",txt, " with ", rgx)
                # Are dates appropriate:
                    if DateConverter.__qualify(date1,date2):
                        arr.append((date1,date2, m[0].strip()))
                        # remove found sequence from search string:
                        txt=txt.replace(m[0],' ')
                    elif DateConverter.__qualify(date2,date1):
                        arr.append((date2,date1, m[0].strip()))
                        # remove found sequence from search string:
                        txt=txt.replace(m[0],' ')
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
        st=[DateConverter.__toTimespan(m[0],m[1],m[2]) for m in arr]
        
        return st
    
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
        # (date1,date2)=DateConverter.__generateMonth([args[0],args[2]])
        # (dateX,date2)=DateConverter.__generateMonth([args[1],args[2]])
        # return (date1,date2)
    
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
                print('Erroneous date {}-{}-{} replaced with: {}'.format(yy,mm,dd,dt))
            else:
                print('{}:\t{}-{}-{}'.format(e,yy,mm,dd))
        return dt
    
    @staticmethod
    def __lastDayOfMonth(date2):
        while True:
            if date2.day==1:
                date2+=datetime.timedelta(days=-1)
                break
            else:
                date2+=datetime.timedelta(days=1)
        return date2
    
    @staticmethod
    def __entireTimespan(arr):
        # choose earliest and latest date
        # from a list of datetime.dates:
        return (min([x[0] for x in arr]),
                max([x[-1] for x in arr]))
    


    