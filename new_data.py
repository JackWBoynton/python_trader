import wget
import datetime
import glob
import gzip
import pandas as pd
import argparse

def download_new(location):

    date = datetime.date.today() - datetime.timedelta(days=1)
    if location+date.strftime("%Y%m%d")+'.csv' not in glob.glob(location+'2019*.csv'):
        print('downloading new days data')
        wget.download(url="https://s3-eu-west-1.amazonaws.com/public.bitmex.com/data/quote/{}.csv.gz".format(date.strftime('%Y%m%d')), out=location)
        input = gzip.GzipFile(location+date.strftime("%Y%m%d")+'.csv.gz', 'rb')
        s = input.read()
        input.close()
        output = open(location+date.strftime("%Y%m%d")+'.csv', 'wb')
        output.write(s)
        output.close()
        # Parse:
        print('\nparsing')
        asset = 'XBTUSD'
        data = pd.read_csv(location+date.strftime("%Y%m%d")+'.csv', header=None, low_memory=False, usecols=[0, 1, 3], dtype={0: str, 1: str, 3: float}, skiprows=2)
        for n, j in enumerate(data[1]):
            if j == asset:
                data = pd.DataFrame(data.values[n:])
                break
        for n, k in enumerate(data[1]):
            if k != asset:
                data = pd.DataFrame(data.values[:n])
                break
        del data[1]
        data.to_csv(location+date.strftime("%Y%m%d")+'.csv')
        print('done')
        return 1
    else:
        print('have all data')
        return 0


def download_abs(day):
    day = str(day)
    print(day)
    print("https://s3-eu-west-1.amazonaws.com/public.bitmex.com/data/quote/{}.csv.gz".format(day))
    wget.download(url="https://s3-eu-west-1.amazonaws.com/public.bitmex.com/data/quote/{}.csv.gz".format(day), out='../')
    input = gzip.GzipFile("../"+day+".csv.gz", 'rb')
    s = input.read()
    input.close()
    output = open("../"+day+".csv","wb")
    output.write(s)
    output.close()
    print("\nparsing")
    asset = "XBTUSD"
    data = pd.read_csv("../"+day+'.csv', header=None, low_memory=False, usecols=[0, 1, 3], dtype={0: str, 1: str, 3: float}, skiprows=2)
    for n, j in enumerate(data[1]):
        if j == asset:
            data=pd.DataFrame(data.values[n:])
            break
    for n, k in enumerate(data[1]):
        if k != asset:
            data=pd.DataFrame(data.values[:n])
            break
    del data[1]
    data.to_csv("../"+day+".csv")
    print("done")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('day', type=str, nargs=1)
    args = parser.parse_args()
    download_abs(args.day[0])
