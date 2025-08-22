import requests
from lxml import html
import pandas as pd
import os
from datetime import date

from define_collection_wave import folder
from helpers import create_folder, cleanhtml

path_benjerry = create_folder('39_BenJerry', folder)


headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en-US,en;q=0.9,en-IN;q=0.8',
    'cache-control': 'max-age=0',
    'priority': 'u=0, i',
    'sec-ch-ua': '"Chromium";v="130", "Microsoft Edge";v="130", "Not?A_Brand";v="99"',
    'sec-ch-ua-mobile': '?1',
    'sec-ch-ua-platform': '"Android"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36 Edg/130.0.0.0',
}
#
base_url = 'https://www.benjerry.co.uk/flavours'

response = requests.get(base_url, headers=headers)
sc = html.fromstring(response.text)

all_categories_links = sc.xpath("//section//a[contains(text(),'View All')]/@href")
for all_category_link in all_categories_links:
    category_response = requests.get('https://www.benjerry.co.uk'+all_category_link , headers=headers)
    sc1 = html.fromstring(category_response.text)
    category_name = ''.join(sc1.xpath("//h1/text()"))
    all_products_link = sc1.xpath('//div[@class="flavor-card"]//a/@href')

    for all_product_link in all_products_link:
        product_response = requests.get('https://www.benjerry.co.uk' + all_product_link, headers=headers)
        sc2 = html.fromstring(product_response.text)

        try:
            product_name = ''.join(sc2.xpath("//h1/text()"))
        except:
            product_name = ''
        try:
            product_description = ''.join(sc2.xpath("//section[@class='flavor-about']/div//text()"))
        except:
            product_description = ''
        try:
            ingredients = ''.join(sc2.xpath("//button[contains(text(),'Ingredients')]/parent::h3/following-sibling::div//p//text()")).replace('Ingredients:','').replace('\n','').strip()
        except:
            ingredients = ''
        try:
            ingredient_image ='https://www.benjerry.co.uk/'+ ''.join(sc2.xpath("//button[contains(text(),'Ingredients')]/parent::h3/following-sibling::div//img/@src"))
        except:
            ingredient_image = ''
        data = {
            'collection_date': date.today().strftime("%b-%d-%Y"),
            'rest_name': "Ben & Jerry's",
            'category_name' : category_name,
            'product_name' : product_name,
            'product_description' : product_description,
            'ingredients' : ingredients,
            'ingredient_image' : ingredient_image
        }
        df = pd.DataFrame([data])
        if os.path.exists(path_benjerry+'/39_BenJerry_items.csv'):
            df.to_csv(path_benjerry+'/39_BenJerry_items.csv', header=False, index=False, mode='a')
        else:
            df.to_csv(path_benjerry+'/39_BenJerry_items.csv', header=True, index=False, mode='a')



# response = requests.get('https://www.benjerry.co.uk/flavours/ice-cream-tubs', headers=headers)
# print(response)



