import requests

data = requests.get('http://132.198.249.205:4444/quote?symbol=XBTUSD')
for i in data:
    
