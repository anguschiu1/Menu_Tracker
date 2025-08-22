import requests
import json
import pandas as pd
from lxml import html
from datetime import  date
import os

from define_collection_wave import folder
from helpers import create_folder

tossed_path = create_folder('80_Tossed', folder)


data_store = []

all_keys = set()

class Tossed:
    def __init__(self):
        self.headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-US,en;q=0.9,en-IN;q=0.8',
            'cache-control': 'no-store, max-age=0',
            'locale': 'null',
            'menu': '642a94ec-bea1-42a2-8ed1-79225c70aad6',
            'origin': 'https://tosseduk.vmos.io',
            'pragma': 'no-cache',
            'priority': 'u=1, i',
            'referer': 'https://tosseduk.vmos.io/',
            'sec-ch-ua': '"Chromium";v="130", "Microsoft Edge";v="130", "Not?A_Brand";v="99"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'store': '34412cca-f374-497a-be27-f134e7693c34',
            'tenant': '87a1a7de-18ef-4dcf-b105-45105792347a',
            'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36 Edg/130.0.0.0',
            'x-requested-from': 'online',
        }
        self.menu_url = 'https://vmos2.vmos.io/catalog/v2/menu'

    def scrape(self):
        menu_response = requests.get(self.menu_url , headers=self.headers)
        json_response_menu = json.loads(menu_response.content)
        all_menus = json_response_menu['payload'][0]['categories']
        for menus in all_menus:
            uuid = menus['uuid']
            menu_name = menus['name']
            product_request_url = requests.get(f'https://vmos2.vmos.io/catalog/categories/{uuid}/bundles',headers=self.headers)
            products_json_response = json.loads(product_request_url.content)
            try:
                all_categories = products_json_response['payload']['categories']
            except:
                all_categories = []

            if all_categories:
                for category in all_categories:
                    all_products = category['bundles']
                    self.product_fn(all_products,menu_name)
            else:
                all_products_1 = products_json_response['payload']['bundles']
                self.product_fn(all_products_1,menu_name)

        df = pd.DataFrame(data_store)
        if os.path.exists(tossed_path+ '/80_tossed1.csv'):
            df.to_csv(tossed_path+ '/80_tossed1.csv', header=False, index=False, mode='a')
        else:
            df.to_csv(tossed_path+ '/80_tossed1.csv', header=True, index=False, mode='a')

    def product_fn(self,all_products,menu_name):
        global all_keys, data_store
        for product in all_products:
            try:
                product_name = product['name']
            except:
                product_name = ''

            try:
                product_description = product['description'].replace('<p>','').replace('</p>','').replace('&nbsp;',' ').replace('&amp;','').replace('\n','').replace('<br>','').strip()
            except:
                product_description = ''
            try:
                nutritionalMeta = product['items'][0]['nutritionalMeta']
            except:
                nutritionalMeta = ''
            data = {}
            data.update({
                'rest_name': 'Tossed',
                'collection_date': date.today().strftime("%b-%d-%Y"),
                'menu_section': menu_name,
                'item_name' : product_name,
                'item_description' : product_description,
            })
            all_keys.update(nutritionalMeta.keys())
            ne = {key: nutritionalMeta.get(key, None) for key in all_keys}

            data.update(ne)
            print(data)

            data_store.append(data)



if __name__ == '__main__':
    web_scrape = Tossed()
    web_scrape.scrape()