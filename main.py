import time

import requests
import csv
from pathlib import Path
import datetime
from settings import settings

import dbus
import logging
from logging.handlers import RotatingFileHandler
import sys
import os

sys.path.insert(1, os.path.join(os.path.dirname(__file__), 'ext', 'velib_python'))
from vedbus import VeDbusItemImport

class GetLoadSheddingStatus:

    def __init__(self, dbus):
        self.bus = dbus
        self.loadsheddingdict = {}
        self.cwd = Path(__file__).parent
        self.starttimes = []
        self.csvlist = []
        self.currentlsvalue = 0
        self.updatelsvaltime = datetime.datetime.now()

        # Ensure this is at the end of the init
        self.loadcsv(settings['filename'], settings['blocknumber'])

    def loadcsv(self, filename, block_number):
        csvpath = self.cwd.joinpath('data', filename)
        with open(csvpath, mode='r') as csv_file:
            csv_reader = csv.DictReader(csv_file, delimiter=',')
            for row in list(csv_reader):
                self.csvlist.append(row)
            # Create the list with the start times in integer format
            for row in self.csvlist:
                if round(float(row['Start time'])*24) not in self.starttimes:
                    self.starttimes.append(round(float(row['Start time'])*24))
            days = []
            # Create the list of days in integer format
            for key in self.csvlist[0].keys():
                if key.isdigit():
                    days.append(int(key))
            # Calculate and create the list of loadshedding numbers
            for day in days:
                self.loadsheddingdict[day] = {}
                for time in self.starttimes:
                    self.loadsheddingdict[day][time] = 99
                for row in self.csvlist:
                    if int(row[str(day)]) == block_number:
                        current_starttime = round(round(float(row['Start time'])*24))
                        self.loadsheddingdict[day][current_starttime] = int(row['Loadshedding number'])
            # print(self.loadsheddingdict[1])

    def updateloadsheddingvalue(self):
        api_endpoint = "http://loadshedding.eskom.co.za/LoadShedding/GetStatus"
        try:
            response = requests.get(api_endpoint).text
            # loadsheddingstatus = -1
            if int(response) >= 1:
                loadsheddingstatus = int(response) - 1
            self.currentlsvalue = loadsheddingstatus
            mainlogger.debug(f'Currently loadshedding level {self.currentlsvalue}')
            mainlogger.debug('Updated loadsheddingvalue')
            self.updatelsvaltime = datetime.datetime.now() + settings['lsvalupdatetime']
        except:
            mainlogger.warning('Failed to update loadsheddingvalue')


    # def lsvalue(self, day, hour):
    #     # Find the starttime that is smaller than the hour value sent
    #     smaller_starttime = 0
    #     for index, starttime in enumerate(self.starttimes):
    #         if hour > starttime :
    #             smaller_starttime = self.starttimes[index]
    #             break
    #     return self.loadsheddingdict[day][smaller_starttime]
    #
    # def lsactive(self, day, hour):
    #     self.updateloadsheddingvalue()
    #     if self.currentlsvalue >= self.lsvalue(day=day, hour=hour):
    #         return True
    #     else:
    #         return False

    def lstimes(self):
        # self.updateloadsheddingvalue()
        today = (datetime.datetime.now() + settings['timezoneoffset'] ).day
        tomorrow = (datetime.datetime.now() + settings['timezoneoffset'] + datetime.timedelta(days=1)).day
        lstimes = {today: [],
                   tomorrow: []}
        for day in lstimes.keys():
            mainlogger.debug(f'Loadsheddingdict: {self.loadsheddingdict[day]}')
            for time, lslevel in self.loadsheddingdict[day].items():
                if self.currentlsvalue >= int(lslevel):
                    t = datetime.time(hour=time)
                    lsstarttime =  datetime.datetime.combine((datetime.datetime.now() + settings['timezoneoffset']).date() , t)
                    lsstarttime = lsstarttime.replace(day=day)
                    if datetime.datetime.now() + settings['timezoneoffset'] <= lsstarttime + settings['loadsheddingduration']:
                        lstimes[day].append(time)
            mainlogger.debug(f'Lstimes: {[lstimes[today], lstimes[tomorrow]]}')
        return[lstimes[today], lstimes[tomorrow]]

    def nextlstime(self):
        lstimes = self.lstimes()
        # lstimes = [[], [13, 22]]
        today = (datetime.datetime.now() + settings['timezoneoffset']).date()
        tomorrow = today + datetime.timedelta(days=1)
        for time in lstimes[0]:
            t = datetime.time(hour=time)
            return datetime.datetime.combine(today, t)
        for time in lstimes[1]:
            t = datetime.time(hour=time)
            return datetime.datetime.combine(tomorrow, t)
        return (datetime.datetime.now() + datetime.timedelta(days=365))

    def get_dbus(self, service):
        dictionary = settings['dbusservices']
        try:
            val = VeDbusItemImport(
                bus=self.bus,
                serviceName=dictionary[service]['Service'],
                path=dictionary[service]['Path'],
                eventCallback=None,
                createsignal=False).get_value()
            mainlogger.debug(f'Got value {val} for {service}')
        except dbus.DBusException:
            mainlogger.warning('Exception in getting dbus service %s' % service)
        try:
            val *= 1
        except:
            mainlogger.warning(f'Non numeric value on {service}')
            # Use the default value as in settings.py
            val = settings['dbusservices'][service]['value']
        return val

    def set_dbus(self, service, value):
        dictionary = settings['dbusservices']
        try:
            VeDbusItemImport(
                bus=self.bus,
                serviceName=dictionary[service]['Service'],
                path=dictionary[service]['Path'],
                eventCallback=None,
                createsignal=False).set_value(value)
            mainlogger.info(f'Successfully set {service} to value of {value}')
        except dbus.DBusException:
            mainlogger.warning('Exception in setting dbus service %s' % service)

    def run(self):
        while True:
            # Update the loadsheddingvalue if required
            if self.updatelsvaltime <= datetime.datetime.now() + settings['timezoneoffset']:
                self.updateloadsheddingvalue()
            # Check if loadshedding will start soon and disconnect if so
            if datetime.datetime.now() + settings['timezoneoffset'] >= self.nextlstime() - settings['predisconnecttime']:
                if int(self.get_dbus('systemmode')) != 2:
                    self.set_dbus('systemmode', 2)
            # Else reconnect
            elif int(self.get_dbus('systemmode')) != 3:
                self.set_dbus('systemmode', 3)
            time.sleep(settings['sleeptime'])



# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    def create_rotating_log(path):
        # Create the logger
        logger = logging.getLogger('loadsheddingchecker')
        logger.setLevel(logging.DEBUG)
        # Create a rotating filehandler
        filehandler = RotatingFileHandler(path, maxBytes=settings['logsize'], backupCount=1)
        filehandler.setLevel(settings['fileloglevel'])
        # Create a streamhandler to print to console
        consolehandler = logging.StreamHandler()
        consolehandler.setLevel(logging.DEBUG)
        # Create a formatter and add to filehandler and consolehandler
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        filehandler.setFormatter(formatter)
        consolehandler.setFormatter(formatter)
        # Add the filehandler and consolehandler to the logger
        logger.addHandler(filehandler)
        logger.addHandler(consolehandler)
        return logger

    # setup the logger
    log_file = "log.txt"
    mainlogger = create_rotating_log(log_file)
    # Setup the dbus
    # DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()
    # start the controller

    checker = GetLoadSheddingStatus( dbus=bus)
    # print(obj.lsvalue(day=1, hour=1))
    # print(obj.lsactive(day=1,hour=1))
    # print(obj.lstimes())
    # print(checker.nextlstime())
    while True:
        try:
            mainlogger.info('Starting Loadsheddingchecker')
            checker.run()
        except:
            mainlogger.exception(f'Error on main program')
            time.sleep(60)