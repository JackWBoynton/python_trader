import json


def new_trade(past_bricks, price_open, price_close, side, macd_open, macd_close, sma_open, sma_close, time_open, time_close):
    string = ''
    for i in past_bricks:
        string += str(i) + ','
    for j in macd_open:
        string += str(j[0]) + ','
    for k in sma_open:
        string += str(k[0]) + ','

    if side == 1 and price_close > price_open:
        profit = 1
    elif side == 0 and price_open > price_close:
        profit = 1
    else:
        profit = 0

    with open('data-raw.csv', 'a') as f:
        f.write(string + str(price_open) + ',' + str(price_close) + ',' + str(side) + ',' + str(macd_open[0]) + ',' + str(macd_close[0]) +
                ',' + str(sma_open[0]) + ',' + str(sma_close[0]) + ',' + str(time_open) + ',' + str(time_close) + ',' + str(profit) + '\n')

    with open('data-clean.csv', 'a') as f:
        # STRING: past_bricks(10),macd_open(10),sma_open(10),price_open,profitable?
        f.write(string + str(price_open) + ',' + str(profit) + '\n')
