import requests
from helpers import create_folder
import json
from define_collection_wave import folder
import pandas as pd

path_wetherspoons = create_folder('2_Wetherspoons',folder)

def wetherspoonsCrawler(pub_id):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36',
    'authorization': 'Bearer e3a3f707b51cf98660f536f7474dd4f1f3f0155d',

        'referer': 'https://allergens.jdwetherspoon.com/',
        'APIKey': 'YVB5QfeRKUK1+EGvXGjPgQA93reRTUJHsCuQSHR+=='}
    url = f'https://api.order.jdwetherspoon.com/api/v1/allergens/pubs/{pub_id}/food'
    resp = requests.get(url, headers=headers)
    items = resp.json()
    data_ = items['data']
    fileName = path_wetherspoons + '/pub_' + str(pub_id) + '.json'
    with open(fileName, 'w') as f:
        json.dump(items, f)
    return pd.DataFrame(data_)

wetherspoon = wetherspoonsCrawler(pub_id=70)
wetherspoon.to_csv(path_wetherspoons + '/Wetherspoons_items.csv')
