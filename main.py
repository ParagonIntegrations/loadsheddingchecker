import requests
import csv
from pathlib import Path


class GetLoadSheddingStatus:

    def __init__(self, filename, block_number):
        self.loadsheddingdict = {}
        self.cwd = Path(__file__).parent
        self.starttimes = []
        self.csvlist = []
        self.currentlsvalue = 0
        # Ensure this is at the end of the init
        self.loadcsv(filename, block_number)

    def loadcsv(self, filename, block_number):
        csvpath = self.cwd.joinpath('data').joinpath(filename)
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
                    self.loadsheddingdict[day][time] = 9
                for row in self.csvlist:
                    if int(row[str(day)]) == block_number:
                        current_starttime = round(round(float(row['Start time'])*24))
                        self.loadsheddingdict[day][current_starttime] = int(row['Loadshedding number'])
            print(self.loadsheddingdict[1])

    def updateloadsheddingvalue(self):
        api_endpoint = "http://loadshedding.eskom.co.za/LoadShedding/GetStatus"
        try:
            response = requests.get(api_endpoint).text
            loadsheddingstatus = -1
            if int(response) >= 1:
                loadsheddingstatus = int(response) - 1
            self.currentlsvalue = loadsheddingstatus
            return 'Updated loadsheddingvalue'
        except:
            return 'Failed to update loadsheddingvalue'


    def lsvalue(self, day, hour):
        # Find the starttime that is smaller than the hour value sent
        smaller_starttime = 0
        for index, starttime in enumerate(self.starttimes):
            if hour > starttime :
                smaller_starttime = self.starttimes[index]
                break
        return self.loadsheddingdict[day][smaller_starttime]

    def lsactive(self, day, hour):
        self.updateloadsheddingvalue()
        if self.currentlsvalue >= self.lsvalue(day=day, hour=hour):
            return True
        else:
            return False


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    file = "NorthWest_LS.csv"
    obj = GetLoadSheddingStatus(filename=file, block_number=5)
    # print(obj.lsvalue(day=1, hour=1))
    print(obj.lsactive(day=1,hour=1))


