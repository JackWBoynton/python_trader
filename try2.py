#!/usr/local/bin/python3
import websocket
import time
import urllib
import json
import hmac
import hashlib
import I2C_DRIVER
import pymysql.cursors
import requests

# This is up to you, most use microtime but you may have your own scheme so long as it's increasing
# and doesn't repeat.
API_KEY = "EB_-_4uDVClVJp9IsxqrmsHY"
API_SECRET = "1g6pMg7bp4Z9hL1lFqgC3Xt2PxMj35HLrJMJKH2QQ6Cgc94L"

BITMEX_URL = "wss://www.bitmex.com"

VERB = "GET"
ENDPOINT = "/realtime"

mylcd = I2C_DRIVER.lcd()
initial_bal = 0.010721
last_price = 0


def on_message(ws, message):
    message = json.loads(message)
    # print (message)
    if message['table'] == 'position':
        mylcd.lcd_clear()
        mylcd.lcd_display_string(
            "c_trade " + str(round(float(message['data'][0]['unrealisedRoePcnt']) * 100, 2)) + '%', 3)
    elif message['table'] == 'margin':
        #mylcd.lcd_clear()
        mylcd.lcd_display_string("funds: $%s" % str(round(float(message['data'][0]['marginBalance']) / 100000000 * float(
            requests.get("https://www.bitmex.com/api/v1/orderBook/L2?symbol=xbt&depth=1").json()[1]['price']), 2)), 1)
        mylcd.lcd_display_string("funds: %s BTC" % str(
            round(float(message['data'][0]['marginBalance']) / 100000000, 6)), 2)
        bal = float(message['data'][0]['marginBalance']) / 100000000
        mylcd.lcd_display_string("net: %s" % str(
            round((bal - initial_bal) / initial_bal * 100, 2)) + '%', 4)
    elif message['table'] == 'quote':
        print (message)

        connection = pymysql.connect(host='localhost', user='jackboynton',
                                     password='BwJ130903!', db='raw', cursorclass=pymysql.cursors.DictCursor)
        with connection.cursor() as cursor:
            # Create a new record
            sql = "SELECT * FROM `ticks`"
            cursor.execute(sql, ())
            data = cursor.fetchall()

            sql = "INSERT INTO `ticks` (`bid_price`) VALUES (%s)"

            cursor.execute(sql, (message['data'][0]['bidPrice']))
            # connection is not autocommit by default. So you must commit to save
            # your changes.
            connection.commit()
            connection.close()


def on_error(ws, error):
    print(error)


def on_close(ws):
    start()


def on_open(ws):
    request = {"op": "subscribe", "args": "position"}
    ws.send(json.dumps(request))
    request = {"op": "subscribe", "args": "margin"}
    ws.send(json.dumps(request))
    request = {"op": "subscribe", "args": ["quote:XBTUSD"]}
    ws.send(json.dumps(request))
    print("Sent subscribe")
    # ws.close()


def bitmex_signature(apiSecret, verb, url, nonce, postdict=None):
    """Given an API Secret key and data, create a BitMEX-compatible signature."""
    data = ''
    if postdict:
        # separators remove spaces from json
        # BitMEX expects signatures from JSON built without spaces
        data = json.dumps(postdict, separators=(',', ':'))
    parsedURL = urllib.parse.urlparse(url)
    path = parsedURL.path
    if parsedURL.query:
        path = path + '?' + parsedURL.query
    # print("Computing HMAC: %s" % verb + path + str(nonce) + data)
    message = (verb + path + str(nonce) + data).encode('utf-8')
    # print("Signing: %s" % str(message))

    signature = hmac.new(apiSecret.encode('utf-8'), message,
                         digestmod=hashlib.sha256).hexdigest()
    # print("Signature: %s" % signature)
    return signature

def start():
    expires = int(time.time()) + 5000000000 + 5000000000
    # See signature generation reference at https://www.bitmex.com/app/apiKeys
    signature = bitmex_signature(API_SECRET, VERB, ENDPOINT, expires)

    # Initial connection - BitMEX sends a welcome message.
    ws = websocket.WebSocketApp(BITMEX_URL + ENDPOINT +
                                "?api-expires=%s&api-signature=%s&api-key=%s" % (expires, signature, API_KEY), on_message=on_message, on_close=on_close, on_error=on_error)
    ws.on_open = on_open
    ws.run_forever(ping_interval=10)

if __name__ == '__main__':
    start()
