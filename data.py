import json


def new_trade(past_bricks, price_open, price_close, side, macd_open, macd_close, sma_open, sma_close, time_open, time_close):
    string = ''
    for i in past_bricks:
        string += str(i) + ','
    if side == 1 and price_close > price_open:
        profit = 1
    elif side == 0 and price_open > price_close:
        profit = 1
    else:
        profit = 0

    with open('data.csv', 'a') as f:
        f.write(string + str(price_open) + ',' + str(price_close) + ',' + str(side) + ',' + str(macd_open) + ',' + str(macd_close) +
                ',' + str(sma_open) + ',' + str(sma_close) + ',' + str(time_open) + ',' + str(time_close) + ',' + str(profit) + '\n')
