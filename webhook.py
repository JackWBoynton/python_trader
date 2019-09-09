#!/usr/local/bin/python3

# TradingView alerts post to this webhook and trades are placed on seperate python threads

import sys
from flask import Flask, request, abort
import time
from engines import BitmexTrader, BinanceTrader, RobinhoodTrader, AlpacaTrader
import pymysql.cursors
import threading
import logging
import configparser
Config = configparser.ConfigParser()
Config.read("config.ini")

log = logging.getLogger('werkzeug')
log.disabled = True

trade = BitmexTrader(trade=True, leverage=3, tp=0.5, test=False)
simulator = BitmexTrader(trade=False, leverage=3, tp=0.03, test=True)
binance = BinanceTrader()
#robin = RobinhoodTrader()
alpaca = AlpacaTrader()

app = Flask(__name__)


@app.route('/', methods=['POST'])
def webhook():
    # print("webhook");
    sys.stdout.flush()
    #print (request)
    if request.method == 'POST':
        #print (str(request))
        alert = (request.data).decode()
        threading.Thread(target=trade.post_balance, args=()).start()
        if 'BUY:BITMEX:XBTUSD' in alert:
            threading.Thread(target=addtt, args=(
                'BUY:BITMEX:XBTUSD', )).start()

            threading.Thread(target=trade.buy_long, args=(
                "BITMEX", "XBT-USD", )).start()
        elif "SELL:BITMEX:XBTUSD" in alert:
            threading.Thread(target=addtt, args=(
                "SELL:BITMEX:XBTUSD", )).start()
            threading.Thread(target=trade.sell_short,
                             args=("BITMEX", "XBT-USD", )).start()
        elif "BUY:BINANCE:BNBUSDT" in alert:
            threading.Thread(target=binance.buy_long, args=()).start()
        elif "SELL:BINANCE:BNBUSDT" in alert:
            threading.Thread(target=binance.sell_short, args=()).start()
        elif "SELL:ROBINHOOD" in alert:
            #threading.Thread(target=robin.sell_short, args=(alert.split(':')[2]))
            pass
        elif "SELL:ROBINHOOD:CHK" in alert:
            #threading.Thread(target=robin.buy_long, args=(alert.split(':')[2]))
            pass
        elif "BUY:ALPACA:" in alert:
            print(alert)
            threading.Thread(target=alpaca.buy_long, args=(alert.split(':')[2]))
        elif "SELL:ALPACA:" in alert:
            print(alert)
            threading.Thread(target=alpaca.sell_short, args=(alert.split(':')[2]))
        else:
            print(alert)
            pass
        return '', 200
    else:
        abort(400)


def delete():
    connection = pymysql.connect(host='localhost', user='jackboynton',
                                 password='BwJ130903!', db='raw', cursorclass=pymysql.cursors.DictCursor)
    with connection.cursor() as cursor:
        # Create a new record
        sql = "DELETE FROM `ticks`"
        cursor.execute(sql, ())

    connection.commit()
    connection.close()


def addtt(string):

    connection = pymysql.connect(host='localhost', user=Config.get('Db', 'user'), password=Config.get(
        'Db', 'password'), db='updates', cursorclass=pymysql.cursors.DictCursor)
    with connection.cursor() as cursor:
        # Create a new record
        sql = "INSERT INTO `orders` (`data`) VALUES (%s)"
        cursor.execute(sql, (string))

    # connection is not autocommit by default. So you must commit to save
    # your changes.
    connection.commit()
    connection.close()


if __name__ == '__main__':
    print('starting webhook')
    app.run(host='127.0.0.1', port=7777)
