import pandas as pd
import wget
import gzip
import glob
import argparse
import os


def fix_absolute(filename, location='../'):
    if filename not in glob.glob(location+'2019*.csv'):
        print('fixing...')
        print('downloading new data for: ' + str(filename))
        wget.download(url="https://s3-eu-west-1.amazonaws.com/public.bitmex.com/data/quote/{}.gz".format(filename), out=location)
        input = gzip.GzipFile(filename+'.gz', 'rb')
        s = input.read()
        input.close()
        output = open(filename, 'wb')
        output.write(s)
        output.close()
        # Parse:
        print('parsing')
        asset = 'XBTUSD'
        data = pd.read_csv(location+filename+'.csv', header=None, low_memory=False, usecols=[0, 1, 3], dtype={0: str, 1: str, 3: float}, skiprows=2)
        for n, j in enumerate(data[1]):
            if j == asset:
                data = pd.DataFrame(data.values[n:])
                break
        for n, k in enumerate(data[1]):
            if k != asset:
                data = pd.DataFrame(data.values[:n])
                break
        del data[1]
        data.to_csv(location+filename+'.csv')
        print('done')
        return 1
    else:
        os.remove(filename)
        fix_absolute(filename)


def fix(filename):
    # called from other functions
    print('fix')


if __name__ == '__main__':
    # if called from commandline
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", nargs=1, type=str)
    args = parser.parse_args()

    fix_absolute(args.filename)
