import json
from datetime import date
from time import sleep
import scrapy
# from browserPath import web_browser_path
from scrapy import Selector
from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options # Import Options
from fake_useragent import UserAgent


class A5KfcSpider(scrapy.Spider):
    name = '5_KFC'
    allowed_domains = ['www.kfc.co.uk/nutrition-allergens']
    start_urls = ['https://www.kfc.co.uk/nutrition-allergens?close']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
          # s = Service(web_browser_path)
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage") # Add this line
        self.driver = webdriver.Chrome(options=chrome_options)
        self.user_agent = UserAgent()

    def parse(self, response):
        self.driver.get(response.url)
        sleep(2)
        page_source = Selector(text = self.driver.page_source)
        self.driver.quit()
        dat = json.loads(page_source.xpath('//script[@id="__NEXT_DATA__"]/text()').get())
        items = dat.get('props').get('pageProps').get('data').get('mainContent')[2].get('data').get("children").get("products")
        for item in items:
            allergens = item.get('allergens')
            allergen_list = [allergen for allergen in allergens.keys() if allergens.get(allergen).get('type') is not False]
            # this list includes primary and secondary allergens (not sure what it means)
            nutrients = item.get('nutrition')
            vegan = item.get('vegan')
            vegetarian = item.get('vegetarian')
            item_dict =  {
                'rest_name': 'KFC',
                'collection_date': date.today().strftime("%b-%d-%Y"),
                'item_name': item.get('name'),
                'menu_section': item.get('categories')[0],
                'allergens': allergen_list,
                'vegan': vegan,
                'vegetarian': vegetarian
            }
            item_dict.update(nutrients)
            yield item_dict
