from math import floor

from ruamel.std.zipfile import InMemoryZipFile
from zipfile import ZipFile
from .libraries.slpp import dcsslpp as lua
from datetime import datetime
from pyproj import Proj

WRITEACCESS_ERROR = 'This file is write-protected!'
class WriteProtectionError(Exception):
    pass

class MIZFile(object):
    MIZfilename = ''
    readonly = True
    missionData = None
    missionLua = None
    theatre = None
    projection = None
    projectiondata = {}
    projectiondata['Caucasus'] = {}
    projectiondata['Caucasus']['utmzone'] = "36"
    projectiondata['Caucasus']['northing'] = 4998115
    projectiondata['Caucasus']['easting'] = 599517
    projectiondata['Caucasus']['hemi'] = 'north'
    projectiondata['Nevada'] = {}
    projectiondata['Nevada']['utmzone'] = "11"
    projectiondata['Nevada']['northing'] = 4410028.064
    projectiondata['Nevada']['easting'] = 693996.81
    projectiondata['Nevada']['hemi'] = 'north'
    projectiondata['Normandy'] = {}
    projectiondata['Normandy']['utmzone'] = "30"
    projectiondata['Normandy']['northing'] = 5484813
    projectiondata['Normandy']['easting'] = 695526
    projectiondata['Normandy']['hemi'] = 'north'
    projectiondata['PersianGulf'] = {}
    projectiondata['PersianGulf']['utmzone'] = "40"
    projectiondata['PersianGulf']['northing'] = 2894932.9363
    projectiondata['PersianGulf']['easting'] = 424243.9786
    projectiondata['PersianGulf']['hemi'] = 'north'
    projectiondata['Syria'] = {}
    projectiondata['Syria']['utmzone'] = "37"
    projectiondata['Syria']['northing'] = 3879865
    projectiondata['Syria']['easting'] = 217198
    projectiondata['Syria']['hemi'] = 'north'
    projectiondata['TheChannel'] = {}
    projectiondata['TheChannel']['utmzone'] = "31"
    projectiondata['TheChannel']['northing'] = 5636888
    projectiondata['TheChannel']['easting'] = 400623
    projectiondata['TheChannel']['hemi'] = 'north'

    def __init__(self, filename, readonly=True):
        self.MIZfilename = filename
        self.readonly = readonly

    def commit(self):
        if self.readonly:
            raise WriteProtectionError(WRITEACCESS_ERROR)
        mizfilehandle = InMemoryZipFile(self.MIZfilename)
        mizfilehandle.delete_from_zip_file(None, 'mission')
        mizfilehandle.append('mission', lua.encode(self.missionData)[1:-1].encode('UTF-8'))
        mizfilehandle.write_to_file(self.MIZfilename)

    def getMissionLUA(self):
        if not self.missionLua:
            mizfilehandle = ZipFile(self.MIZfilename, mode='r')
            missionfilehandle = mizfilehandle.open('mission', 'r')
            self.missionLua = missionfilehandle.read()
            missionfilehandle.close()
        return self.missionLua

    def getMission(self):
        if not self.missionData:
            self.missionData = lua.decode('{' + self.getMissionLUA().decode('UTF-8') + '}')
        return self.missionData['mission']

    def setMission(self, missiondata):
        if self.readonly:
            raise WriteProtectionError(WRITEACCESS_ERROR)
        self.missionData['mission'] = missiondata

    def getTheatre(self):
        if self.theatre:
            return self.theatre
        mizfilehandle = ZipFile(self.MIZfilename, mode='r')
        try:
            theatrefilehandle = mizfilehandle.open('theatre', 'r')
            self.theatre = theatrefilehandle.read().decode('UTF-8')
        except KeyError:
            #Could be the newer MIZ format where the theatre file is no longer extra
            self.theatre = self.getMission()["theatre"]
        return self.theatre
    
    def getProjectionData(self):
        return self.projectiondata[self.getTheatre()]
        
    def getProjection(self):
        if self.projection:
            pass
        else:
            self.projection = Proj("+proj=utm +zone="+self.getProjectionData()['utmzone']+" +"+self.getProjectionData()['hemi']+" +ellps=WGS84 +datum=WGS84 +units=m +no_defs")
        return self.projection

    def getProjectedXY(self, lat, lon):
        y, x = self.getProjection()(lon, lat)
        return (x-self.getProjectionData()['northing'],y-self.getProjectionData()['easting'])
        
    def getProjectedLatLon(self, x, y):
        lon, lat = self.getProjection()(y+self.getProjectionData()['easting'], x+self.getProjectionData()['northing'],inverse=True)
        return (lat, lon)
        
    def getTheatreLatLon(self):
        if self.getTheatre() == 'Caucasus':
            return {"lat": 42.355691, "lon": 43.323853}
        elif self.getTheatre() == 'PersianGulf':
            return {"lat": 26.304151 , "lon": 56.378506}
        elif self.getTheatre() == 'Nevada':
            return {"lat": 36.145615, "lon": -115.187618}
        elif self.getTheatre() == 'Normandy':
            return {"lat": 49.183336, "lon": -0.365908}
        elif self.getTheatre() == 'Syria':
            return {"lat": 35.140901, "lon": 36.051701}
        elif self.getTheatre() == 'TheChannel':
            return {"lat": 50.945076, "lon": -0.365908}
        else:
            return None

    def getDateTime(self):
        day = self.getMission()['date']['Day']
        month = self.getMission()['date']['Month']
        year = self.getMission()['date']['Year']
        starttime = self.getMission()['start_time']
        second = floor(starttime % 60)
        starttime /= 60
        minute = floor(starttime % 60)
        hour = floor(starttime / 60)
        datestr = f'{day:02}' + '.' + f'{month:02}' + '.' + f'{year:04}' + ' ' + f'{hour:02}' + ':' + f'{minute:02}'\
                  + ':' + f'{second:02}'
        return datetime.strptime(datestr, '%d.%m.%Y %H:%M:%S')

    def setDateTime(self, dt):
        if self.readonly:
            raise WriteProtectionError(WRITEACCESS_ERROR)
        missiondata = self.getMission()
        missiondata['date']['Day'] = dt.day
        missiondata['date']['Month'] = dt.month
        missiondata['date']['Year'] = dt.year
        missiondata['start_time'] = (((dt.hour*60) + dt.minute)*60) + dt.second
        self.setMission(missiondata)

    def setDateTimeNow(self):
        self.setDateTime(datetime.now())

    def getWeather(self):
        return self.getMission()['weather']

    def setWeather(self, weatherdata):
        if self.readonly:
            raise WriteProtectionError(WRITEACCESS_ERROR)
        missiondata = self.getMission()
        missiondata['weather'] = weatherdata
        self.setMission(missiondata)
