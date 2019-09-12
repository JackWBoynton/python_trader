#!/usr/local/bin/python3
import websocket
import time
import urllib
import json
import hmac
import hashlib
import slack

import configparser
Config = configparser.ConfigParser()
Config.read("config.ini")
client = slack.WebClient(Config.get("Slack", 'api_key'), timeout=30)



# This is up to you, most use microtime but you may have your own scheme so long as it's increasing
# and doesn't repeat.
API_KEY = "EB_-_4uDVClVJp9IsxqrmsHY"
API_SECRET = "1g6pMg7bp4Z9hL1lFqgC3Xt2PxMj35HLrJMJKH2QQ6Cgc94L"

BITMEX_URL = "wss://www.bitmex.com"

VERB = "GET"
ENDPOINT = "/realtime"

initial_bal = 0.010721
last_price = 0
runs = 0

def on_message(ws, message):
    message = json.loads(message)
    print (message)
    if message['table'] == 'position':
        pos = round(float(message['data'][0]['unrealisedRoePcnt']) * 100, 2)
    elif message['table'] == 'margin':

        bal = float(message['data'][0]['marginBalance']) / 100000000
        runs += 1
        if runs > 0:
            net = round((bal - initial_bal) / initial_bal * 100, 2)
            try:
                client.chat_postMessage(channel='balance_updates', text='net: ' + str(net) + '%' + ' current: ' + str(pos) + '%')
            except Exception as e:
                print(str(e))
            runs = 0


def on_error(ws, error):
    print(error)


def on_close(ws):
    start()


def on_open(ws):
    request = {"op": "subscribe", "args": "position"}
    ws.send(json.dumps(request))
    request = {"op": "subscribe", "args": "margin"}
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
    ws.run_forever(ping_interval=1)

if __name__ == '__main__':
    start()
