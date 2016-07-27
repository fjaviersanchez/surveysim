from astropy.time import Time, TimezoneInfo
from datetime import datetime
from datetime import date
import astropy.units as u
import numpy as np
from pkg_resources import resource_filename

"""
Line format
0, 1, 2: evening day, month, date
3: /
4, 5, 6: morning day, month, date
7: MJD of local midnight
8, 9, 10: LMST of midnight hours, minutes, seconds
11, 12: Sun set hours, minutes
13, 14: evening twilight end hours, minutes
15, 16: morning twilight begin hours, minutes
17, 18: Sun rise hours, minutes
19, 20: evening twilight LST hours, minutes
21, 22: morning twilight LST hours, minutes

Case 1 (Moon rise and set times are both given)
 23, 24: Moon rise hours, minutes
 25, 26: Moon set hours, minutes
 27: Moon illumination fraction
 28, 29: Moon RA hours, minutes
 Case 1a:
  30, 31: Moon DEC degrees, minutes
 Case 1b
  30, 31, 32: - Moon DEC degrees, minutes

Case 2 (Moon rise or Moon set not given)
 23: .....                         OR  23, 24: Moon rise hours, minutes
 24, 25: Moon set hours, minutes   OR  25: .....
 26: Moon illumination fraction
 27, 28: Moon RA hours, minutes
 Case 2a:
  29, 30: Moon DEC degrees, minutes
 Case 1b
  29, 30, 31: - Moon DEC degrees, minutes
"""
daymonth0 = np.array([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
daymonthLeap = np.array([31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])

def monthNum(monthname):
    month = 0
    if monthname == 'Jan': month = 1
    elif monthname == 'Feb': month = 2
    elif monthname == 'Mar': month = 3
    elif monthname == 'Apr': month = 4
    elif monthname == 'May': month = 5
    elif monthname == 'Jun': month = 6
    elif monthname == 'Jul': month = 7
    elif monthname == 'Aug': month = 8
    elif monthname == 'Sep': month = 9
    elif monthname == 'Oct': month = 10
    elif monthname == 'Nov': month = 11
    elif monthname == 'Dec': month = 12
    return month

def obsCalendar(day1, month1, year1, day2, month2, year2):
    if year1 < 2016:
        print "Warning: calendar available only from 2016;"
        print "resetting start date to 1 January 2016."
        day1 = 1
        month1 = 1
        year1 = 2016
    if year2 > 2025:
        print "Warning: calendar available only up to 2025;"
        print "resetting end date to 31 December 2025."
        day2 = 31
        month2 = 12
        year2 = 2025
    date1 = date(year1, month1, day1)
    date2 = date(year2, month2, day2)
    utc_minus7 = TimezoneInfo(utc_offset=-7*u.hour)
    cal = []
    for year in range(year1, year2+1):
        calfile = 'data/calendar.' + str(year)
        if np.mod(year,4) == 0 and np.mod(year,400) != 0:
            daymonth = daymonthLeap
        else:
            daymonth = daymonth0
        with open(resource_filename('surveysim', calfile),'r') as f:
            while True:
                line = f.readline()
                if not line: break
                if line[0] == '#': continue
                entries = line.split()
                month = monthNum(entries[1])
                day = int(entries[2])
                datenow = date(year, month, day)
                if datenow >= date1 and datenow <= date2:
                    JDtruncated = float(entries[7])
                    # These conditions work only for year 2016-2025
                    if year <= 2022 or (year == 2023 and month < 3):
                        MJDmidnight = JDtruncated + 2450000.0 - 2400000.5
                    if (year == 2023 and month >= 3) or year > 2024:
                        MJDmidnight = JDtruncated + 2460000.0 - 2400000.5
                    sunset_h = int(entries[11])
                    sunset_m = int(entries[12])
                    Tsunset = Time(datetime(year, month, day, sunset_h, sunset_m, 0, tzinfo=utc_minus7))
                    etwi_h = int(entries[13])
                    etwi_m = int(entries[14])
                    Tetwi = Time(datetime(year, month, day, etwi_h, etwi_m, 0, tzinfo=utc_minus7))
                    mtwi_h = int(entries[15])
                    mtwi_m = int(entries[16])
                    yearnew = year
                    monthnew = month
                    daynew = day + 1
                    if daynew > daymonth[month-1]:
                        daynew = 1
                        monthnew = month + 1
                    if monthnew > 12:
                        monthnew = 1
                        yearnew = year +1
                    Tmtwi = Time(datetime(yearnew, monthnew, daynew, mtwi_h, mtwi_m, 0, tzinfo=utc_minus7))
                    sunrise_h = int(entries[17])
                    sunrise_m = int(entries[18])
                    Tsunrise = Time(datetime(yearnew, monthnew, daynew, sunrise_h, sunrise_m, 0, tzinfo=utc_minus7))
                    if entries[23] == "....." or entries[25] == ".....": # Either Moon rise or set time not given
                        if entries[23] == ".....":
                            MJDmoonrise = -1.0
                            moonset_h = int(entries[24])%24 # forces the hour to be between 0..23
                            moonset_m = int(entries[25])
                            yearnew = year
                            monthnew = month
                            daynew = day
                            if moonset_h < 12:
                                daynew = day + 1
                                if daynew > daymonth[month-1]:
                                    daynew = 1
                                    monthnew = month + 1
                                    if monthnew > 12:
                                        monthnew = 1
                                        yearnew = year +1
                            MJDmoonset = (Time(datetime(yearnew, monthnew, daynew, moonset_h, moonset_m, 0, tzinfo=utc_minus7))).mjd
                        else:
                            MJDmoonset = -1.0
                            moonrise_h = int(entries[23])%24 # forces the hour to be between 0..23
                            moonrise_m = int(entries[24])
                            yearnew = year
                            monthnew = month
                            daynew = day
                            if moonrise_h < 12:
                                daynew = day + 1
                                if daynew > daymonth[month-1]:
                                    daynew = 1
                                    monthnew = month + 1
                                    if monthnew > 12:
                                        monthnew = 1
                                        yearnew = year +1
                            MJDmoonrise = (Time(datetime(yearnew, monthnew, daynew, moonrise_h, moonrise_m, 0, tzinfo=utc_minus7))).mjd
                        moonIllum = float(entries[26])
                        moonRA = float(entries[27]) + float(entries[28])/60.0
                        moonRA = moonRA * 15.0
                        if entries[29] == "-":
                            moonDEC = -1.0 * (float(entries[30]) + float(entries[31])/100.0)
                        else:
                            moonDEC = float(entries[29]) + float(entries[30])/100.0
                    else: # Both Moon rise and set times are given
                        moonrise_h = int(entries[23])
                        moonrise_m = int(entries[24])
                        yearnew = year
                        monthnew = month
                        daynew = day
                        if moonrise_h < 12:
                            daynew = day + 1
                            if daynew > daymonth[month-1]:
                                daynew = 1
                                monthnew = month + 1
                                if monthnew > 12:
                                    monthnew = 1
                                    yearnew = year +1
                        MJDmoonrise = (Time(datetime(yearnew, monthnew, daynew, moonrise_h, moonrise_m, 0, tzinfo=utc_minus7))).mjd
                        moonset_h = int(entries[25])
                        moonset_m = int(entries[26])
                        yearnew = year
                        monthnew = month
                        daynew = day
                        if moonset_h < 12:
                            daynew = day + 1
                            if daynew > daymonth[month-1]:
                                daynew = 1
                                monthnew = month + 1
                                if monthnew > 12:
                                    monthnew = 1
                                    yearnew = year +1
                        MJDmoonset = (Time(datetime(yearnew, monthnew, daynew, moonset_h, moonset_m, 0, tzinfo=utc_minus7))).mjd
                        moonIllum = float(entries[27])
                        moonRA = float(entries[28]) + float(entries[29])/60.0
                        if entries[30] == "-":
                            moonDEC = -1.0 * (float(entries[31]) + float(entries[32])/100.0)
                        else:
                            moonDEC = float(entries[30]) + float(entries[31])/100.0
                    # Get the night's directory name right away.
                    if month >= 10:
                        monthStr = str(month)
                    else:
                        monthStr = '0' + str(month)
                    if day >= 10:
                        dayStr = str(day)
                    else:
                        dayStr = '0' + str(day)
                    dirName = str(year) + monthStr + dayStr
                    cal.append( {'MJDmidnight': MJDmidnight,
                                 'MJDsunset': Tsunset.mjd,
                                 'MJDsunrise': Tsunrise.mjd,
                                 'MJDetwi': Tetwi.mjd,
                                 'MJDmtwi': Tmtwi.mjd,
                                 'MJDmoonrise': MJDmoonrise,
                                 'MJDmoonset': MJDmoonset,
                                 'MoonFrac': moonIllum,
                                 'MoonRA': moonRA,
                                 'MoonDEC': moonDEC,
                                 'dirName': dirName} )
        f.close()
    return cal
