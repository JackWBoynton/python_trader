import math



class trader:
    
    def __init__(self, bal):
        self._bal = bal
        self.bal_btc = bal
        self.open_contracts_usd = 0
        self.risk = 0.6 # risk 60% of capital, fee comes out of btc bal after trade comes out
        self.long = False
        self.short = False
        self.leverage = 10
        self.fee = 0.0075 # 0.075%
    
    def buy(self, price):
        assert not self.long and self.open_contracts_usd == 0
        self.long = True
        self.open_price = price
        buying_power = math.floor(self.bal_btc * price * self.risk) * self.leverage  # num contracts can buy --> USD
        fee = round((buying_power * self.fee) / price, 8)
        self.bal_btc -= fee
        self.open_contracts_usd = buying_power
        print(f"bought {buying_power} contracts with {self.leverage}x leverage, fee: {fee} BTC, at {price}")

    def sell(self, price):
        assert not self.short and self.open_contracts_usd == 0
        self.short = True
        self.open_price = price
        selling_power = math.floor(self.bal_btc * price * self.risk) * self.leverage
        fee = round((selling_power * self.fee) / price,8)
        self.bal_btc -= fee
        self.open_contracts_usd = selling_power
        print(f"shorted {selling_power} contracts with {self.leverage}x leverage, fee: {fee} BTC, at {price}")

    def close(self, price):
        assert self.long or self.short
        if self.short:
            profit = (1/self.open_price)-(1/price)
            profit *= -self.open_contracts_usd
            self.short = False
        elif self.long:
            profit = (1 / self.open_price) - (1 / price)
            profit *= self.open_contracts_usd
            self.long = False
        fee = round((self.open_contracts_usd * self.fee) / price, 8)
        self.bal_btc -= abs(fee)
        self.bal_btc += round(profit,8)
        self.bal_btc += round((self.open_contracts_usd/self.leverage) / price,8)
        self.open_contracts_usd = 0
        print(f"closed trade at {price}, profit: {profit} BTC, bal after: {self.bal_btc}, fee: {fee} BTC")

    def end(self,price):
        if self.long or self.short:
            self.close(price)
        print(f"end, change: {self.bal_btc - self._bal} BTC")

