#!/usr/bin/env python

# Parse the NCDC station list and generated a tab-delimited file of station
# station-CCAFS region pairs, e.g. "029070-99999<tab>A4". Usage:
#
#   python gen_station_regions.py < isd-history.csv > station_regions.txt

from datetime import datetime
import re
import sys

# Get CCAFS region corresponding to station coordinates, or D for anything
# outside regions A1-C6. The idealised CCAFS region boundaries are:
#
#      180W     120W     60W       0       60E      120E     180E
#  90N  +--------+--------+--------+--------+--------+--------+
#       |   A1   |   A2   |   A3   |   A4   |   A5   |   A6   |
#  40N  +--------+--------+--------+--------+--------+--------+
#       |   B1   |   B2   |   B3   |   B4   |   B5   |   B6   |
#  10S  +--------+--------+--------+--------+--------+--------+
#       |   C1   |   C2   |   C3   |   C4   |   C5   |   C6   |
#  60S  +--------+--------+--------+--------+--------+--------+
#       |                          D                          |
#  90S  +-----------------------------------------------------+
#
def get_region(lat, lon):
    # CCAFS longitudes are in the half-open interval [-180, +180) while
    # NCDC ones are in (-180, +180] so map NCDC's +180 to CCAFS's -180 and
    # vice-versa (the latter is to catch any invalid NCDC latitudes of -180).
    if abs(lon) == 180:
        lon = -lon
    # CCAFS regions cover latitudes 60 S to 90 N inclusive
    if lat < -60 or lat > 90 or lon < -180 or lon > 179:
        return "D"
    else:
        # Derive region from given coordinates. 90 N is outside the idealised
        # region A latitudes of [+40, +90), but included because CCAFS cells
        # are slightly taller than their nominal 30 arc second height due to
        # round-off. The repeated "A" accounts for this anomaly.
        return "CBAA"[(lat + 60) / 50] + str((lon + 180) / 60 + 1)

def main():
    # Valid station IDs are the six-digit USAF catalogue number followed by
    # the five-digit WBAN number
    valid_id = re.compile("^\d{6}-\d{5}$")
    print "# Generated by {0} at {1} using data".format(sys.argv[0],
        datetime.today().ctime())
    print "# from ftp://ftp.ncdc.noaa.gov/pub/data/noaa/isd-history.csv"
    line_num = 0
    for line in sys.stdin:
        line_num += 1
        # Skip header line
        if line_num == 1:
            continue
        fields = line.split(",")
        if len(fields) < 8:
            sys.stderr.write("Too few fields on line {0}\n".format(line_num))
            continue
        # Strip surrounding quotes off the first two fields in the CSV input
        # then concatenate them to form the station ID 
        station = "{0}-{1}".format(fields[0][1:-1], fields[1][1:-1])
        if not valid_id.match(station):
            sys.stderr.write("Invalid station '{0}' on line {1}\n".
                             format(station, line_num))
            continue
        try:
            # Python doesn't let us truncate towards negative infinity so
            # we adjust the coordinates to be non-negative, then undo the
            # adjustment after truncation 
            lat = int(float(fields[6][1:-1]) + 90) - 90
            lon = int(float(fields[7][1:-1]) + 180) - 180
            region = get_region(lat, lon)
        except:
            # Lots of stations are missing coordinates, so default to region D
            region = 'D'
        print "{0}\t{1}".format(station, region)

if __name__ == "__main__":
    main()
