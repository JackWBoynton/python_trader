import pandas as pd
import xgboost as xgb
from sklearn.externals import joblib
scaler_filename = "../scaler.save"
scaler = joblib.load(scaler_filename)

bst = xgb.Booster({'nthread': 4})  # init model
bst.load_model('../0001.model')  # load data


def main(ys, macd, sma, last_price):
    string = []
    for i in ys:
        string.append(i)
    for j in macd:
        string.append(j[0])
    for k in sma:
        string.append(k[0])
    string.append(0)
    string.append(last_price)
    #print(string)
    string = pd.DataFrame(string)
    print(string)
    string = scaler.transform(string)
    return bst.predict(xgb.DMatrix(string))[0]
