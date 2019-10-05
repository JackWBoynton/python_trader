import wget
import datetime
import glob
import gzip


def download_new():
    date = datetime.date.today() - datetime.timedelta(days=1)
    if '../'+date.strftime("%Y%m%d")+'.csv' not in glob.glob('../2019*.csv'):
        wget.download(url="https://s3-eu-west-1.amazonaws.com/public.bitmex.com/data/quote/{}.csv.gz".format(date.strftime('%Y%m%d')), out='../')
        input = gzip.GzipFile("../"+date.strftime("%Y%m%d")+'.csv.gz', 'rb')
        s = input.read()
        input.close()
        output = open("../"+date.strftime("%Y%m%d")+'.csv', 'wb')
        output.write(s)
        output.close()
        return 1
    else:
        return 0


def download_abs(day):
    day = str(day)+'.csv'
    wget.download(url="https://s3-eu-west-1.amazonaws.com/public.bitmex.com/data/quote/{}.csv.gz".format(day), out='../')
    return 1
