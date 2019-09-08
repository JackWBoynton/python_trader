#!/usr/local/bin/python3

# This file contains all of the trading logic

import time
import json
from math import floor
import slack
import bitmex
import requests
from binance.client import Client as binance_client
import pymysql.cursors
import robin_stocks as r
import os
import alpaca_trade_api as tradeapi
import configparser
Config = configparser.ConfigParser()
Config.read("config.ini")  # load api_keys

API_KEY = "PK9NQMLQ6JQIUVEHNMLR"
API_SECRET = "t9bh74YO5jPhKbo3EA0yQoLYfaedU/2Jg79NTzqS"
APCA_API_BASE_URL = "https://paper-api.alpaca.markets"


class AlpacaTrader():
    def __init__(self):
        self.auth_client_alpaca = tradeapi.REST(Config.get('Alpaca', 'api_key'), Config.get('Alpaca','api_secret'),APCA_API_BASE_URL, api_version='v2') # or use ENV Vars shown below
        self.account = self.auth_client_alpaca.get_account()
        self.equity = float(self.account.equity)

    def buy_long(self, asset):
        try:
            self.auth_client_alpaca.submit_order(symbol=asset,qty=10,side='buy',type='market',time_in_force='gtc')
        except Exception as e:
            print (str(e))
        finally:
            print ('buying 10 ' + str(asset) + ' on ALPACA')

    def sell_short(self, asset):
        try:
            self.auth_client_alpaca.submit_order(symbol=asset,qty=10,side='sell',type='market',time_in_force='gtc')
        except Exception as e:
            print (str(e))
        finally:
            print ('selling 10 ' + str(asset) + ' on ALPACA')

class BitmexTrader():

    def __init__(self, trade, leverage, tp, test):
        self.bitmex_api_key = Config.get('Bitmex', 'api_key')
        self.bitmex_api_secret = Config.get('Bitmex', 'api_secret')
        self.bitmex_api_key_t = Config.get('Bitmex-Testnet', 'api_key')
        self.bitmex_api_secret_t = Config.get('Bitmex-Testnet', 'api_secret')
        self.slack_api = Config.get("Slack", 'api_key')
        self.trade = trade
        self.leverage = leverage
        self.take_profit = tp
        self.stop_loss = 0.1 # 10%
        self.db_user = Config.get("Db", 'user')
        self.db_pass = Config.get("Db", 'password')
        if test:
            self.auth_client_bitmex = bitmex.bitmex(
                test=True, api_key=self.bitmex_api_key_t, api_secret=self.bitmex_api_secret_t)
        else:
            self.auth_client_bitmex = bitmex.bitmex(
                test=False, api_key=self.bitmex_api_key, api_secret=self.bitmex_api_secret)
        try:
            self.auth_client_bitmex.Position.Position_updateLeverage(
                symbol='XBTUSD', leverage=leverage).result()
        except:
            pass
        self.last_bal = float(self.auth_client_bitmex.User.User_getMargin().result()[
                              0]['marginBalance'] / 100000000)
        self.channel = 'tradeupdates'
        self.channel_trades = 'trades'
        self.client = slack.WebClient(self.slack_api, timeout=30)
        self.open = {'side': '', 'price': 0, 'qty': 0, 'close': 0}
        if trade:
            if not os.path.isfile('orders.csv'):
                with open('orders.csv', 'w'):
                    pass
            self.filename = 'orders.csv'
        else:
            if not os.path.isfile('sim_orders.csv'):
                with open('sim_orders.csv', 'w'):
                    pass
            self.test_bal = 0.002
            self.test_open_qty = 0
            self.open_price = 0
            self.filename = 'sim_orders.csv'

    def gui(self, op, take, stop, qty):

        connection = pymysql.connect(host='localhost', user=self.db_user,
                                     password=self.db_pass, db='orders', cursorclass=pymysql.cursors.DictCursor)
        with connection.cursor() as cursor:
            # Create a new record
            sql = "INSERT INTO `trades` (`open_price`,`take_price`,`stop_price`,`qty`) VALUES (%s,%s,%s,%s)"
            cursor.execute(sql, (op, take, stop, qty))

        # connection is not autocommit by default. So you must commit to save
        # your changes.
        connection.commit()
        connection.close()

    def order(self, dictt):
        with open(self.filename, 'a') as f:
            f.write(json.dumps(dictt) + '\n')
        return {'side': '', 'price': 0, 'qty': 0, 'close': 0}

    def post_balance(self):
        try:
            self.client.chat_postMessage(channel=self.channel_trades, text='current bal: ' + str(
                (self.auth_client_bitmex.User.User_getMargin().result()[0]['marginBalance'] / 100000000)*float(requests.get("https://www.bitmex.com/api/v1/orderBook/L2?symbol=xbt&depth=1").json()[1]['price'])))
        except:
            pass
        return ''

    def buy_long(self, ex, pair):
        pair = pair.split('-')
        if self.trade:
            self.client.chat_postMessage(
                channel=self.channel, text='BUY:BITMEX:XBTUSD')
        if ex == 'BITMEX':
            if self.trade:
                self.auth_client_bitmex.Order.Order_cancelAll().result()
                close = self.auth_client_bitmex.Order.Order_new(
                    symbol='XBTUSD', ordType='Market', execInst='Close').result()
                new_bal = float(self.auth_client_bitmex.User.User_getMargin().result()[
                                0]['marginBalance'] / 100000000)
                time.sleep(5)
                f = open(self.filename, 'r')
                r = f.readlines()
                if len(r) > 0 and json.loads(r[-1])['close'] == 0 and json.loads(r[-1])['side'] == 'short':
                    try:
                        self.client.chat_postMessage(channel=self.channel_trades, text='closed short at ' + str(close[0]['price']) + '. profit: $' + str(round(
                            (new_bal - self.last_bal) * float(requests.get("https://www.bitmex.com/api/v1/orderBook/L2?symbol=xbt&depth=1").json()[1]['price']), 3)))
                        self.open['price'] = close[0]['price']
                        self.open['side'] = 'null'
                        self.open['qty'] = close[0]['orderQty']
                        self.open['close'] = 1
                        self.open = self.order(self.open)
                    except:
                        pass

            else:
                if self.test_open_qty < 0 and self.open_price > 0:
                    profit = ((1 / float(requests.get("https://www.bitmex.com/api/v1/orderBook/L2?symbol=xbt&depth=1").json()[
                              1]['price'])) - (1 / self.open_price)) * -self.test_open_qty
                    fee = profit * 0.00075
                    profit = profit - fee
                    self.test_bal = self.test_bal + profit
                print(str(self.test_bal))
                self.open['price'] = float(requests.get(
                    "https://www.bitmex.com/api/v1/orderBook/L2?symbol=xbt&depth=1").json()[1]['price'])
                self.open['side'] = 'null'
                self.open['qty'] = 'prev'
                self.open['close'] = 1
                self.open = self.order(self.open)

            # time.sleep(2)
            bal = self.auth_client_bitmex.User.User_getMargin().result()[
                0]['availableMargin'] / 100000000
            response = requests.get(
                "https://www.bitmex.com/api/v1/orderBook/L2?symbol=xbt&depth=1").json()
            time.sleep(2)
            price = float(response[1]['price'])
            order_q = floor(bal * self.leverage * price) - 10

            if self.trade:

                try:
                    order = self.auth_client_bitmex.Order.Order_new(
                        symbol='XBTUSD', orderQty=order_q).result()
                    time.sleep(2)
                    ord = order[0]['ordStatus']
                except Exception as e:
                    self.auth_client_bitmex.Order.Order_cancelAll().result()
                    close = self.auth_client_bitmex.Order.Order_new(
                        symbol='XBTUSD', ordType='Market', execInst='Close').result()
                    print(str(e) + ' retrying...')
                    self.client.chat_postMessage(channel=self.channel_trades, text='error: ' + str(e) + ' retrying...')
                    time.sleep(2)
                    ord = ''

                print('buy order: ' + str(ord))

                self.auth_client_bitmex.Order.Order_new(symbol='XBTUSD', ordType='MarketIfTouched', stopPx=floor(
                    price * (1 + self.take_profit / self.leverage) * 0.5) / 0.5, orderQty=-order_q).result()
                self.auth_client_bitmex.Order.Order_new(symbol='XBTUSD', ordType='Stop', stopPx=floor(
                    (price - (price * self.stop_loss / self.leverage)) * 0.5) / 0.5, orderQty=-order_q).result()
                print('placed tp at: ' + str(floor(price *
                                                   (1 + self.take_profit / self.leverage) * 0.5) / 0.5))
                print('placed sl at: ' + str(floor((price -
                                                    (price * self.stop_loss / self.leverage)) * 0.5) / 0.5))

                self.last_bal = float(self.auth_client_bitmex.User.User_getMargin().result()[0]['marginBalance'] / 100000000)
                self.client.chat_postMessage(channel=self.channel_trades, text='bought: ' + str(round(float(order[0]['orderQty']) / self.leverage,3)) + ' XBT with ' + str(self.leverage) + ' X leverage at $' + str(order[0]['price']))

                self.gui(op=order[0]['price'], take=floor(price * (1 + self.take_profit / self.leverage) * 0.5) /0.5, stop=floor((price - (price * self.stop_loss / self.leverage)) * 0.5) / 0.5, qty=order_q)
                self.open['price'] = order[0]['price']
                self.open['side'] = 'long'
                self.open['qty'] = order[0]['orderQty']
                self.open['close'] = 0
                self.open = self.order(self.open)
            else:
                self.open['price'] = price
                self.open_price = price
                self.open['side'] = 'long'
                self.open['qty'] = floor(
                    self.test_bal * self.leverage * price) - 10
                self.open['close'] = 0
                self.open = self.order(self.open)
                self.test_open_qty = floor(
                    self.test_bal * self.leverage * price) - 10

        print('bought long on bitmex: ' + str(order_q) +
              ' @ ' + str(order[0]['price']))

    def sell_short(self, ex, pair):

        try:
            pair = pair.split('-')
            if self.trade:
                self.client.chat_postMessage(
                    channel=self.channel, text='SELL:BITMEX:XBTUSD')
            if ex == 'BITMEX':
                if self.trade:

                    self.auth_client_bitmex.Order.Order_cancelAll().result()
                    close = self.auth_client_bitmex.Order.Order_new(
                        symbol='XBTUSD', ordType='Market', execInst='Close').result()
                    new_bal = float(self.auth_client_bitmex.User.User_getMargin().result()[
                                    0]['marginBalance'] / 100000000)
                    time.sleep(5)
                    f = open(self.filename, 'r')
                    r = f.readlines()
                    if len(r) > 0 and json.loads(r[-1])['close'] == 0 and json.loads(r[-1])['side'] == 'long' and close[0]['price']:
                        try:
                            self.client.chat_postMessage(channel=self.channel_trades, text='closed long at ' + str(close[0]['price']) + '. profit: $' + str(round(
                                (new_bal - self.last_bal) * float(requests.get("https://www.bitmex.com/api/v1/orderBook/L2?symbol=xbt&depth=1").json()[1]['price']), 3)))
                            self.last_bal = float(self.auth_client_bitmex.User.User_getMargin().result()[
                                                  0]['marginBalance'] / 100000000)
                            self.open['price'] = close[0]['price']
                            self.open['side'] = 'null'
                            self.open['qty'] = close[0]['orderQty']
                            self.open['close'] = 1
                            self.open = self.order(self.open)
                        except:
                            pass

                response = requests.get(
                    "https://www.bitmex.com/api/v1/orderBook/L2?symbol=xbt&depth=1").json()
                price = float(response[1]['price'])
                bal = self.auth_client_bitmex.User.User_getMargin().result()[
                    0]['availableMargin'] / 100000000

                if self.trade:

                    try:
                        order = self.auth_client_bitmex.Order.Order_new(
                            symbol='XBTUSD', orderQty=-floor(bal * self.leverage * price) + 1).result()
                        time.sleep(2)
                        ord = order[0]['ordStatus']
                    except Exception as e:
                        self.auth_client_bitmex.Order.Order_cancelAll().result()
                        close = self.auth_client_bitmex.Order.Order_new(
                            symbol='XBTUSD', ordType='Market', execInst='Close').result()
                        print(str(e) + ' retrying...')
                        self.client.chat_postMessage(channel=self.channel_trades, text='error: ' + str(e) + ' retrying...')
                        time.sleep(2)
                        ord = ''

                    print('short order: ' + str(ord))

                    self.auth_client_bitmex.Order.Order_new(symbol='XBTUSD', ordType='MarketIfTouched', stopPx=floor(
                        price * (1 - self.take_profit / self.leverage) * 0.5) / 0.5, orderQty=floor(bal * self.leverage * price) + 1).result()
                    self.auth_client_bitmex.Order.Order_new(symbol='XBTUSD', ordType='Stop', stopPx=floor(
                        (price + (price * self.stop_loss / self.leverage)) * 0.5) / 0.5, orderQty=floor(bal * self.leverage * price) + 1).result()
                    print('placed tp at: ' + str(floor(price *
                                                       (1 - self.take_profit / self.leverage) * 0.5) / 0.5))
                    print('placed sl at: ' + str(floor((price + (price *
                                                                 self.stop_loss / self.leverage)) * 0.5) / 0.5))

                    self.client.chat_postMessage(channel=self.channel_trades, text='shorted: ' + str(round(float(-order[0]['orderQty']), 3) / self.leverage) + ' XBT with ' + str(self.leverage) + ' X leverage at $' + str(order[0]['price']))
                    self.open['price'] = order[0]['price']
                    self.open['side'] = 'short'
                    self.open['qty'] = order[0]['orderQty']
                    self.open['close'] = 0
                    self.open = self.order(self.open)
                else:
                    self.open['price'] = price
                    self.open['side'] = 'short'
                    self.open['qty'] = - \
                        floor(self.test_bal * self.leverage * price) + 1
                    self.test_open_qty = - \
                        floor(self.test_bal * self.leverage * price) + 1
                    self.open['close'] = 0
                    self.open = self.order(self.open)

            print('sold short on bitmex: ' +
                  str(order[0]['orderQty']) + ' @ ' + str(order[0]['price']))

        except Exception as e:
            print(e)


class BinanceTrader():
    def __init__(self):
        self.binance_api_key = Config.get('Binance', 'api_key')
        self.binance_api_secret = Config.get('Binance', 'api_secret')
        self.auth_client_binance = binance_client(
            self.binance_api_key, self.binance_api_secret)
        data = self.auth_client_binance.get_symbol_info('BNBUSDT')['filters']
        data = data[5]
        self.min_size = data['minQty']
        self.max_size = data['maxQty']
        self.step = data['stepSize']

    def buy_long(self):
        balance = float(
            self.auth_client_binance.get_asset_balance(asset='USDT')['free'])
        if floor(balance / float(requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BNBUSDT").json()['price']) / 0.01) * 0.01 - 0.01 == 0:
            print('unable to but must sell first')
        else:
            print('qty: ' + str(floor(balance / float(requests.get(
                "https://api.binance.com/api/v3/ticker/price?symbol=BNBUSDT").json()['price']) / 0.01) * 0.01 - 0.01))
            order = self.auth_client_binance.order_market_buy(symbol='BNBUSDT', quantity=floor(
                balance / float(requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BNBUSDT").json()['price']) / 0.01) * 0.01 - 0.01)
            if order['status'] == 'FILLED':
                print('bought ' + str(order['origQty']) +
                      ' at ' + str(order['fills'][0]['price']))
            else:
                print('not confirmed but bought ' + str(floor(balance / float(requests.get(
                    "https://api.binance.com/api/v3/ticker/price?symbol=BNBUSDT").json()['price']) / 0.01) * 0.01 - 0.01) + ' at market price')
        print('bought BNB on Binance')

    def sell_short(self):
        if float(self.auth_client_binance.get_asset_balance(asset='BNB')['free']) > 1:
            selling_power = floor(
                float(self.auth_client_binance.get_asset_balance(asset='BNB')['free']))
        elif float(self.auth_client_binance.get_asset_balance(asset='BNB')['free']) > 0.01:
            selling_power = floor(float(self.auth_client_binance.get_asset_balance(
                asset='BNB')['free']) / 0.01) * 0.01
        else:
            selling_power = 0

        if selling_power != 0:
            order = self.auth_client_binance.order_market_sell(
                symbol='BNBUSDT', quantity=selling_power)
            if order['status'] == 'FILLED':
                print('sold ' + str(order['origQty']) +
                      ' at ' + str(order['fills'][0]['price']))
            else:
                print('not confirmed but sold ' +
                      str(selling_power) + ' at market price')
        else:
            print('unable to sell, must buy first')
        print('sold BNB on Binance')


class RobinhoodTrader():
    def __init__(self):
        self.em = Config.get("Robinhood", "email")
        self.pas = Config.get("Robinhood", 'password')
        r.login(self.em, self.pas)
        self.my_stocks = r.build_holdings()

    def buy_long(self, stock):
        buying_power = float(r.profiles.load_account_profile()[
                             'margin_balances']['day_trade_buying_power'])
        if not self.my_stocks:
            try:
                qty = floor(buying_power /
                            float(r.stocks.get_latest_price(stock)[0]))
                r.order_buy_market(stock, qty)
                print('bought ' + str(qty) + ' : ' + stock)
                self.my_stocks = r.build_holdings()
            except Exception as e:
                print(e)

    def sell_short(self, stock):
        if self.my_stocks:
            try:
                for i in self.my_stocks:
                    if i == stock:
                        bal = float(i['quantity'])
                        r.order_sell_market(stock, bal)
                        print('sold ' + str(bal) + ' : ' + stock)
                        self.my_stocks = r.build_holdings()
            except Exception as e:
                print(e)
