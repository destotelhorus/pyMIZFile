from MIZFile import *

NOTSUPPORTED_ERROR = 'This feature is not supported!'
class NotSupportedError(Exception):
    pass

class STMFile(MIZFile):
    def __init__(self, filename: str, readonly: bool=True):
        super().__init__(filename, readonly)

    def commit(self):
        if self.readonly:
            raise WriteProtectionError(WRITEACCESS_ERROR)
        stmfilehandle = open(self.MIZfilename, "wb")
        stmfilehandle.write('staticTemplate ='.encode('UTF-8'))
        stmfilehandle.write("\n".encode('UTF-8'))
        stmfilehandle.write(lua.encode(self.missionData['staticTemplate']).encode('UTF-8'))
        stmfilehandle.close()

    def getMissionLUA(self):
        if not self.missionLua:
            stmfilehandle = open(self.MIZfilename, 'rb')
            self.missionLua = stmfilehandle.read()
            stmfilehandle.close()
        return self.missionLua

    def getMission(self):
        if not self.missionData:
            self.missionData = lua.decode('{' + self.getMissionLUA().decode('UTF-8') + '}')
        return self.missionData['staticTemplate']

    def setMission(self, missiondata):
        if self.readonly:
            raise WriteProtectionError(WRITEACCESS_ERROR)
        self.missionData['staticTemplate'] = missiondata

    def getTheatre(self):
        if self.theatre:
            return self.theatre
        self.theatre = self.getMission()['threatre']
        return self.theatre

    def getWeather(self):
        raise NotSupportedError(NOTSUPPORTED_ERROR)

    def setWeather(self, weatherdata):
        raise NotSupportedError(NOTSUPPORTED_ERROR)