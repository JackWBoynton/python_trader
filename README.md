bitmex, robinhood, and binance algoritmic traders

1. runs a webhook that waits for POST requests from tradingview alerts, and trades accordingly
2. implements margin trading and take profit and stop loss placement
3. posts orders to SQL server
4. post order updates and balances to slack channels

to run:

1. pip3 install -r requirements.txt
2. start ./ngrok http 7777
2. python3 webhook.py

to calculate renko bricks locally and perform strategy calculations:

* must have raw bitmex tick data in ../ for backtest

1. python3 calculate_renko.py
