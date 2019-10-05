import wget
import datetime
import glob
import gzip
import pandas as pd


def download_new(location):

    date = datetime.date.today() - datetime.timedelta(days=1)
    if '../'+date.strftime("%Y%m%d")+'.csv' not in glob.glob('../2019*.csv'):
        print('downloading new days data')
        wget.download(url="https://s3-eu-west-1.amazonaws.com/public.bitmex.com/data/quote/{}.csv.gz".format(date.strftime('%Y%m%d')), out=location)
        input = gzip.GzipFile("../"+date.strftime("%Y%m%d")+'.csv.gz', 'rb')
        s = input.read()
        input.close()
        output = open("../"+date.strftime("%Y%m%d")+'.csv', 'wb')
        output.write(s)
        output.close()
        ### Parse:
        print('parsing')
        asset = 'XBTUSD'
        data = pd.read_csv("../"+date.strftime("%Y%m%d")+'.csv', header=None, low_memory=False, usecols=[0, 1, 3], dtype={0: str, 1: str, 3: float}, skiprows=2)
        for n, j in enumerate(data[1]):
            if j == asset:
                data = pd.DataFrame(data.values[n:])
                break
        for n, k in enumerate(data[1]):
            if k != asset:
                data = pd.DataFrame(data.values[:n])
                break
        del data[1]
        data.to_csv("../"+date.strftime("%Y%m%d")+'.csv')
        print('done')
        return 1
    else:
        print('have all data')
        return 0


def download_abs(day):
    day = str(day)+'.csv'
    wget.download(url="https://s3-eu-west-1.amazonaws.com/public.bitmex.com/data/quote/{}.csv.gz".format(day), out='../')
    return 1
