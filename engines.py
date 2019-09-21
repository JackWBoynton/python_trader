#!/usr/local/bin/python3

# This file contains all of the trading logic

import time
from math import floor
import slack
from statistics import mean
import bitmex
import requests
from binance.client import Client as binance_client
import robin_stocks as r
from bravado.exception import HTTPServiceUnavailable, HTTPBadRequest
import alpaca_trade_api as tradeapi
import configparser
import numpy as np
import pymysql
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
        self.long = False
        self.short = False
        print('sending trades? ' + str(self.trade))
        self.leverage = leverage
        self.take_profit = tp
        self.stop_loss = 0.1 # 10%
        self.slips = []

        if test:
            self.auth_client_bitmex = bitmex.bitmex(
                test=True, api_key=self.bitmex_api_key_t, api_secret=self.bitmex_api_secret_t)
            print ('testnet')
        else:
            self.auth_client_bitmex = bitmex.bitmex(
                test=False, api_key=self.bitmex_api_key, api_secret=self.bitmex_api_secret)
            print ('LIVE')
        try:
            self.auth_client_bitmex.Position.Position_updateLeverage(
                symbol='XBTUSD', leverage=leverage).result()
        except:
            pass
        self.last_bal = float(self.auth_client_bitmex.User.User_getMargin().result()[0]['marginBalance'] / 100000000)
        self.channel = 'tradeupdates'
        self.channel_trades = 'trades'
        self.client = slack.WebClient(self.slack_api, timeout=30)
        self.trade_template = {'signal_price':0.0, 'fill_price':0.0, 'quantity':0.0, 'leverage':1, 'side':'', 'timestamp':''}

    def db(self):
        ## TRADE = {'signal_price':float, 'fill_price':float, 'quantity':float, 'leverage':int, 'side',string, 'timestamp':string}
        connection = pymysql.connect(host='localhost',
                             user='root',
                             password='Starluna1',
                             db='trades',
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)
        try:
            with connection.cursor() as cursor:
                # Create a new record
                sql = "INSERT INTO `trades_raw` (`signal_price`, `fill_price`, `quantity`, `leverage`, `side`, `timestamp`) VALUES (%s, %s, %s, %s, %s, %s)"
                cursor.execute(sql, (self.trade_template['signal_price'], self.trade_template['fill_price'], self.trade_template['quantity'], self.trade_template['leverage'], self.trade_template['side'], self.trade_template['timestamp']))

            # connection is not autocommit by default. So you must commit to save
            # your changes.
            connection.commit()

        finally:
            connection.close()



        self.trade_template = {'signal_price':0.0, 'fill_price':0.0, 'quantity':0.0, 'leverage':1, 'side','', 'timestamp':''}

    def buy_long(self, ex, pair, ind, pric):
        if self.trade:
            self.client.chat_postMessage(channel=self.channel, text='BUY:BITMEX:XBTUSD')
            self.auth_client_bitmex.Order.Order_cancelAll().result()
            if self.short:
                close = self.auth_client_bitmex.Order.Order_new(symbol='XBTUSD', ordType='Limit', execInst='Close', price=pric-5, timeInForce='FillOrKill').result()
                time.sleep(1)
                runs = 1
                while close[0]['ordStatus'] != 'Filled':
                    close = self.auth_client_bitmex.Order.Order_new(symbol='XBTUSD', ordType='Limit', execInst='Close', price=pric-(5-runs*0.5), timeInForce='FillOrKill').result()
                    runs += 1
                    time.sleep(1)
                self.short = False
                self.trade_template['signal_price'] = pric
                self.trade_template['fill_price'] = float(close[0]['price'])
                self.trade_template['quantity'] = float(close[0]['orderQty'])
                self.trade_template['leverage'] = self.leverage
                self.trade_template['side'] = 'close'
                self.trade_template['timestamp'] = str(close[0]['timestamp'])
                self.db()
            new_bal = float(self.auth_client_bitmex.User.User_getMargin().result()[0]['marginBalance'] / 100000000)
            try:
                self.client.chat_postMessage(channel=self.channel_trades, text='closed short at ' + str(close[0]['price']) + '. profit: $' + str(round((new_bal - self.last_bal) * float(requests.get("https://www.bitmex.com/api/v1/orderBook/L2?symbol=xbt&depth=1").json()[1]['price']), 3)))
                self.last_bal = float(self.auth_client_bitmex.User.User_getMargin().result()[0]['marginBalance'] / 100000000)
            except:
                pass

            bal = self.auth_client_bitmex.User.User_getMargin().result()[0]['availableMargin'] / 100000000
            price = float(requests.get("https://www.bitmex.com/api/v1/orderBook/L2?symbol=xbt&depth=1").json()[1]['price'])
            order_q = floor(bal * self.leverage * price) - 10

            try:
                print ('trying: ' + str(pric))
                order = self.auth_client_bitmex.Order.Order_new(symbol='XBTUSD', orderQty=order_q, price=pric-3, timeInForce='FillOrKill').result()
                time.sleep(1)
                runs = 1
                while order[0]['ordStatus'] != 'Filled':
                    order = self.auth_client_bitmex.Order.Order_new(symbol='XBTUSD', orderQty=order_q, price=pric-(runs*0.5), timeInForce='FillOrKill').result()
                    runs += 1
                    time.sleep(1)
            except HTTPServiceUnavailable as e:
                self.client.chat_postMessage(channel=self.channel_trades, text='error: ' + str(e) + ' retrying...')
                ord = ''
                while ord != 'Filled':
                    time.sleep(0.6)
                    order = self.auth_client_bitmex.Order.Order_new(symbol='XBTUSD', orderQty=order_q).result()
                    ord = order[0]['ordStatus']
            except HTTPBadRequest as r:
                try:
                    order = self.auth_client_bitmex.Order.Order_new(symbol='XBTUSD', orderQty=order_q-10).result()
                except:
                    self.client.chat_postMessage(channel=self.channel_trades, text='error: ' + str(r) + ' FATAL!!! order not placed')
            finally:
                self.slips.append(float(abs(ind-float(order[0]['price']))/0.5))
                print('bought long on bitmex: ' + str(order[0]['orderQty']) + ' @ ' + str(order[0]['price']), 'slip: $' + str(abs(ind-float(order[0]['price']))), 'ticks: ' + str((ind-float(order[0]['price']))/0.5), 'average tick slip: ' + str(mean(self.slips)))

            try:
                self.auth_client_bitmex.Order.Order_new(symbol='XBTUSD', ordType='MarketIfTouched', stopPx=floor(price * (1 + self.take_profit / self.leverage) * 0.5) / 0.5, orderQty=-order_q).result()
            except HTTPServiceUnavailable:
                print('503 retrying...')
                time.sleep(0.6)
                self.auth_client_bitmex.Order.Order_new(symbol='XBTUSD', ordType='MarketIfTouched', stopPx=floor(price * (1 + self.take_profit / self.leverage) * 0.5) / 0.5, orderQty=-order_q).result()
            finally:
                #print('placed tp at: ' + str(floor(price * (1 + self.take_profit / self.leverage) * 0.5) / 0.5))
                pass

            try:
                self.auth_client_bitmex.Order.Order_new(symbol='XBTUSD', ordType='Stop', stopPx=floor((price - (price * self.stop_loss / self.leverage)) * 0.5) / 0.5, orderQty=-order_q).result()
            except HTTPServiceUnavailable:
                print('503 retrying...')
                time.sleep(0.6)
                self.auth_client_bitmex.Order.Order_new(symbol='XBTUSD', ordType='Stop', stopPx=floor((price - (price * self.stop_loss / self.leverage)) * 0.5) / 0.5, orderQty=-order_q).result()
            finally:
                #print('placed sl at: ' + str(floor((price - (price * self.stop_loss / self.leverage)) * 0.5) / 0.5))
                pass

            self.client.chat_postMessage(channel=self.channel_trades, text='bought: ' + str(round(float(order[0]['orderQty']) / self.leverage, 3)) + ' XBT with ' + str(self.leverage) + ' X leverage at $' + str(order[0]['price']))
            self.long = True
            self.trade_template['signal_price'] = pric
            self.trade_template['fill_price'] = float(order[0]['price'])
            self.trade_template['quantity'] = float(order[0]['orderQty'])
            self.trade_template['leverage'] = self.leverage
            self.trade_template['side'] = 'BUY'
            self.trade_template['timestamp'] = str(order[0]['timestamp'])
            self.db()


    def sell_short(self, ex, pair, ind, pric):
        print (str(pric) + '\n')
        if self.trade:
            self.client.chat_postMessage(channel=self.channel, text='SELL:BITMEX:XBTUSD')
            self.auth_client_bitmex.Order.Order_cancelAll().result()
            '''
            close = self.auth_client_bitmex.Order.Order_new(symbol='XBTUSD', ordType='Limit', execInst='Close', price=pric+5, timeInForce='FillOrKill').result()
            time.sleep(1)
            runs = 1
            while close[0]['ordStatus'] != 'Filled':
                close = self.auth_client_bitmex.Order.Order_new(symbol='XBTUSD', ordType='Limit', execInst='Close', price=pric+(5-runs*0.5), timeInForce='FillOrKill').result()
                runs += 1
                time.sleep(1)
            '''
            if self.long:
                close = self.auth_client_bitmex.Order.Order_new(symbol='XBTUSD', ordType='Limit', execInst='Close', price=pric+5).result()
                time.sleep(1)
                runs = 1
                while close[0]['ordStatus'] != 'Filled':
                    close = self.auth_client_bitmex.Order.Order_new(symbol='XBTUSD', ordType='Limit', execInst='Close', price=pric+(5-runs*0.5), timeInForce='FillOrKill').result()
                    runs += 1
                    time.sleep(1)
                self.long = False
                self.trade_template['signal_price'] = pric
                self.trade_template['fill_price'] = float(close[0]['price'])
                self.trade_template['quantity'] = float(close[0]['orderQty'])
                self.trade_template['leverage'] = self.leverage
                self.trade_template['side'] = 'close'
                self.trade_template['timestamp'] = str(close[0]['timestamp'])
                self.db()
            new_bal = float(self.auth_client_bitmex.User.User_getMargin().result()[0]['marginBalance'] / 100000000)
            try:
                self.client.chat_postMessage(channel=self.channel_trades, text='closed long at ' + str(close[0]['price']) + '. profit: $' + str(round((new_bal - self.last_bal) * float(requests.get("https://www.bitmex.com/api/v1/orderBook/L2?symbol=xbt&depth=1").json()[1]['price']), 3)))
                self.last_bal = float(self.auth_client_bitmex.User.User_getMargin().result()[0]['marginBalance'] / 100000000)
            except:
                pass

            price = float(requests.get("https://www.bitmex.com/api/v1/orderBook/L2?symbol=xbt&depth=1").json()[1]['price'])
            bal = self.auth_client_bitmex.User.User_getMargin().result()[0]['availableMargin'] / 100000000

            '''
            order = self.auth_client_bitmex.Order.Order_new(symbol='XBTUSD', orderQty=order_q, price=pric, timeInForce='FillOrKill').result()
            time.sleep(1)
            runs = 0
            while order[0]['ordStatus'] != 'Filled':
                order = self.auth_client_bitmex.Order.Order_new(symbol='XBTUSD', orderQty=order_q, price=pric-(runs*0.5), timeInForce='FillOrKill').result()
                runs += 1
                time.sleep(1)
            '''
            try:
                order = self.auth_client_bitmex.Order.Order_new(symbol='XBTUSD', orderQty=-floor(bal * self.leverage * price) + 10, price=pric+3, timeInForce='FillOrKill').result()
                time.sleep(1)
                runs = 1
                while order[0]['ordStatus'] != 'Filled':
                    order = self.auth_client_bitmex.Order.Order_new(symbol='XBTUSD', orderQty=-floor(bal * self.leverage * price) + 10, price=pric-(runs*0.5), timeInForce='FillOrKill').result()
                    runs += 1
                    time.sleep(1)
            except HTTPServiceUnavailable as e:
                print(str(e) + ' retrying...')
                self.client.chat_postMessage(channel=self.channel_trades, text='error: ' + str(e) + ' retrying...')
                ord = ''
                while ord != 'Filled':
                    time.sleep(0.6)
                    order = self.auth_client_bitmex.Order.Order_new(symbol='XBTUSD', orderQty=-floor(bal * self.leverage * price) + 10).result()
                    ord = order[0]['ordStatus']
            except HTTPBadRequest as r:
                print('short: ' + str(-floor(bal * self.leverage * price) + 10))
                self.client.chat_postMessage(channel=self.channel_trades, text='error: ' + str(r) + ' FATAL!!! order not placed')
            finally:
                self.slips.append(float(abs(ind-float(order[0]['price']))/0.5))
                print('sold short on bitmex: ' + str(order[0]['orderQty']) + ' @ ' + str(order[0]['price']), 'slip: $' + str(abs(ind-float(order[0]['price']))), 'ticks: ' + str((ind-float(order[0]['price']))/0.5), 'average tick slip: ' + str(mean(self.slips)))

            try:
                self.auth_client_bitmex.Order.Order_new(symbol='XBTUSD', ordType='MarketIfTouched', stopPx=floor(price * (1 - self.take_profit / self.leverage) * 0.5) / 0.5, orderQty=floor(bal * self.leverage * price) + 10).result()
            except HTTPServiceUnavailable:
                print('503 retrying...')
                time.sleep(0.6)
                self.auth_client_bitmex.Order.Order_new(symbol='XBTUSD', ordType='MarketIfTouched', stopPx=floor(price * (1 - self.take_profit / self.leverage) * 0.5) / 0.5, orderQty=floor(bal * self.leverage * price) + 10).result()
            finally:
                #print('placed tp at: ' + str(floor(price *(1 - self.take_profit / self.leverage) * 0.5) / 0.5))
                pass

            try:
                self.auth_client_bitmex.Order.Order_new(symbol='XBTUSD', ordType='Stop', stopPx=floor((price + (price * self.stop_loss / self.leverage)) * 0.5) / 0.5, orderQty=floor(bal * self.leverage * price) + 10).result()
            except HTTPServiceUnavailable:
                print('503 retrying...')
                time.sleep(0.6)
                self.auth_client_bitmex.Order.Order_new(symbol='XBTUSD', ordType='Stop', stopPx=floor((price + (price * self.stop_loss / self.leverage)) * 0.5) / 0.5, orderQty=floor(bal * self.leverage * price) + 10).result()
            finally:
                #print('placed sl at: ' + str(floor((price + (price *self.stop_loss / self.leverage)) * 0.5) / 0.5))
                pass

            self.client.chat_postMessage(channel=self.channel_trades, text='shorted: ' + str(round(float(-order[0]['orderQty']), 3) / self.leverage) + ' XBT with ' + str(self.leverage) + ' X leverage at $' + str(order[0]['price']))
            self.short = True
            self.trade_template['signal_price'] = pric
            self.trade_template['fill_price'] = float(order[0]['price'])
            self.trade_template['quantity'] = float(order[0]['orderQty'])
            self.trade_template['leverage'] = self.leverage
            self.trade_template['side'] = 'SELL'
            self.trade_template['timestamp'] = str(order[0]['timestamp'])
            self.db()



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
