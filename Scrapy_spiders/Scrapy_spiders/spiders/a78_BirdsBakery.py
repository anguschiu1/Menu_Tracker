from time import sleep
from datetime import date

import scrapy
from browserPath import web_browser_path
from scrapy import Selector
from selenium import webdriver



class A78BirdsbakerySpider(scrapy.Spider):
    name = '78_BirdsBakery'
    allowed_domains = ['birdsbakery.com']
    start_urls = ['https://birdsbakery.com/pages/nutrition-and-allergen-data']

    def __init__(self):
        self.driver = webdriver.Chrome(web_browser_path)

    def parse(self, response):
        print(f'url: {response.url}')
        self.driver.get(response.url)
        sleep(5)
    
        items = self.driver.find_elements_by_xpath('//*[@id="nutrition-and-allergen-data-app"]/ul/li/div/div/ul/li/a')
        
        for item in items:
            yield scrapy.Request(url=item.get_attribute('href'), callback=self.parse_item)
        
    def parse_item(self, response):
        print(f'url: {response.url}')
        #print(f'item_name: {response.xpath('//*[@id="shopify-section-template--23124809941295__hero"]/div/h1/text()').get().replace(' data','')}')
        print('item_name: {}'.format(response.xpath('//*[@id="shopify-section-template--23124809941295__hero"]/div/h1/text()').get().replace(' data','')))
        item_dict = {
            'collection_date': date.today().strftime("%b-%d-%Y"),
            'rest_name': 'Birds Bakery',
            # 'menu_section': response.request.meta['cat_name'],
            'allergen': response.xpath('//*[@id="shopify-section-template--23124809941295__nutrition_data_item"]/div/div[1]/div/div[3]/p/text()').get(), 
            'item_name': response.xpath('//*[@id="shopify-section-template--23124809941295__hero"]/div/h1/text()').get().replace(' data',''),
        }
        rows = response.xpath('//*[@id="shopify-section-template--23124809941295__nutrition_data_item"]/div/div[1]/div/div[1]/table/tbody/tr')
        for row in rows:
            item_dict.update({
                row.xpath('./td[1]/text()').get()+'_100':row.xpath('./td[2]/text()').get().strip(' mgkcalJ')
                
            })
        print(f'item_dict: {item_dict}')
        yield item_dict