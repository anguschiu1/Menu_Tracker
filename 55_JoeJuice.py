import requests
import json
import pandas as pd
import os
from datetime import date, time

from define_collection_wave import folder
from helpers import create_folder
path_JoeJuice = create_folder('55_JoeJuice', folder) + '/55_JoeJuice_items.csv'


class JoeJuice:
    def __init__(self):
        self.headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-US,en;q=0.9,en-IN;q=0.8',
            'origin': 'https://www.joejuice.com',
            'referer': 'https://www.joejuice.com/',
            'sec-ch-ua': '"Chromium";v="130", "Microsoft Edge";v="130", "Not?A_Brand";v="99"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36 Edg/130.0.0.0',
            'x-joe-web': 'true',
            'x-joeloyalty-version': '2.7.0',
        }

        self.params = {
            # 'storeId': '5f871bf1-b0d1-4e2a-ac84-31047281cde9',
            'storeId': '186f925b-8932-4195-8e67-6e5d01b8bfc2',
            'type': 'all',
        }

        self.base_url = 'https://joepay-api.joejuice.com/me/products/layout'
        self.data_store = []

    def scrape(self):
        response = requests.get(self.base_url, params=self.params, headers=self.headers)
        all_categories = json.loads(response.text)
        print(f"Total categories: {len(all_categories)}")
        for category in all_categories:
            category_name = category['name']
            print(f"Processing category: {category_name}")
            products = category.get('tiles', [])

            for product in products:
                product_name = product.get('name', '')
                product_description = product.get('description', '')
                product_price = product.get('priceRange', '')
                if isinstance(product_price,list):
                    product_price = product_price[0]
                ingredients = product.get('ingredients', [])
                if not ingredients:
                    continue

                product_id = product.get('id', '')
                nutrition, allergens = self.get_product_details(product_id)

                data = {
                    'collection_date': date.today().strftime("%b-%d-%Y"),
                    'rest_name': 'JOE & THE JUICE',
                    'category_name': category_name,
                    'product_name': product_name,
                    'product_description': product_description,
                    'product_price': product_price,
                    **nutrition,
                    **allergens,
                }
                self.data_store.append(data)

        self.save_to_csv()

    def get_product_details(self, product_id):
        nutrition = {}
        allergens = {}
        max_retries = 3
        retry_delay = 2  # seconds

        each_product_params = {
            # 'storeId': '5f871bf1-b0d1-4e2a-ac84-31047281cde9',
            'storeId': '186f925b-8932-4195-8e67-6e5d01b8bfc2',
        }
        for attempt in range(max_retries):
            try:
                ingredient_response = requests.get(
                    f'https://joepay-api.joejuice.com/me/products/{product_id}',
                    params=each_product_params,
                    headers=self.headers
                )
                product_details = json.loads(ingredient_response.text)
                ingredients = product_details['productVariants'][0].get('ingredients', [])
                break
            except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
                print(f"Attempt {attempt + 1} failed for product {product_id}: {e}")
                if attempt < max_retries - 1:
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    print(f"Max retries exceeded for product {product_id}. Skipping.")
                    return nutrition, allergens  # Return empty dictionaries on failure

        # Nutrition data
        nutrition_data = [{'id': ing['id'], 'ingredientAmount': ing['ingredientAmount']} for ing in ingredients]
        for attempt in range(max_retries):
            try:

                nutrition_response = requests.post(
                    f'https://joepay-api.joejuice.com/me/stores/{self.params["storeId"]}/ingredients/nutrition',
                    headers=self.headers,
                    json=nutrition_data
                )
                nutrition_result = json.loads(nutrition_response.text).get('data', [])
                for nutrient in nutrition_result:
                    nutrition[nutrient['name']] = nutrient['value']
                break
            except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
                print(f"Attempt {attempt + 1} failed for nutrition data: {e}")
                if attempt < max_retries - 1:
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    print(f"Max retries exceeded for nutrition data. Skipping.")
                    return nutrition, allergens
 


        # Allergen data
        for attempt in range(max_retries):
            try:
                allergen_data = [{'id': ing['id']} for ing in ingredients]
                allergen_response = requests.post(
                    f'https://joepay-api.joejuice.com/me/stores/{self.params["storeId"]}/ingredients/allergens',
                    headers=self.headers,
                    json=allergen_data
                )
                allergen_result = json.loads(allergen_response.text)
                for allergen in allergen_result:
                    allergens[allergen['name']] = allergen.get('degree', 'None')
                break
            except (requests.exceptions.RequestException,json.JSONDecodeError) as e:
                print(f"Attempt {attempt + 1} failed for allergen data: {e}")
                if attempt < max_retries - 1:
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    print(f"Max retries exceeded for allergen data. Skipping.")
                    return nutrition, allergens

    def save_to_csv(self):
        # output_dir = '55_JoeJuice_Output'
        # os.makedirs(output_dir, exist_ok=True)
        # output_file = os.path.join(output_dir, '55_JoeJuice.csv')
        #
        # df = pd.DataFrame(self.data_store)
        # if os.path.exists(output_file):
        #     df.to_csv(output_file, header=False, index=False, mode='a')
        # else:
        #     df.to_csv(output_file, header=True, index=False, mode='w')

        df = pd.DataFrame(self.data_store)
        if os.path.exists(path_JoeJuice):
            df.to_csv(path_JoeJuice, header=False, index=False, mode='a')
        else:
            df.to_csv(path_JoeJuice, header=True, index=False, mode='a')


if __name__ == '__main__':
    scraper = JoeJuice()
    scraper.scrape()
