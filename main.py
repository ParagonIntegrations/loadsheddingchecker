import requests
import csv
from pathlib import Path



class GetLoadSheddingStatus:

    def __init__(self, filename):
        self.loadsheddingdict = {}
        self.cwd = Path(__file__).parent
        self.loadcsv(filename)

    def loadcsv(self, filename):
        csvpath = self.cwd.joinpath('data').joinpath(filename)
        print(csvpath)
    def loadsheddingvalue(self):
        api_endpoint = "http://loadshedding.eskom.co.za/LoadShedding/GetStatus"
        response = requests.get(api_endpoint).text
        loadsheddingstatus = -1
        if int(response) >= 1:
            loadsheddingstatus = int(response) - 1
        return loadsheddingstatus

    def main(self):
        ls_val = self.loadsheddingvalue()
        print(ls_val)

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    filename = "NorthWest_LS.csv"
    obj = GetLoadSheddingStatus(filename)
    obj.main()


