from datetime import date
from time import sleep

import scrapy
from browserPath import web_browser_path
from scrapy import Selector
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


class A15WagamamaSpider(scrapy.Spider):
    name = '15_Wagamama'
    allowed_domains = ['www.wagamama.com']
    start_urls = ['https://www.wagamama.com/menu?category=sides-sharing']

    def __init__(self):
        self.driver = webdriver.Chrome(web_browser_path)
        self.data = []

    def parse(self, response):
        print(f"Starting the spider script")
        self.driver.get(response.url)

        # try:
        #     WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="onetrust-accept-btn-handler"]'))).click()
        # except TimeoutException:
        #     self.log("The cookie button was not clickable within 10 seconds or not present.")
    
        category_buttons = WebDriverWait(self.driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, '//button[contains(@class, "_menuItemButton_1etan_2")]')))
        for button in category_buttons:
            self.driver.execute_script("arguments[0].click();", button)
            sleep(3)

            food_buttons = self.driver.find_elements(By.XPATH, '//div[contains(@class, "_bottom_pqbyt_34")]//button[contains(@class, "_customButton_157z5_2")]')
            for food_button in food_buttons:
                try:
                    WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(food_button))
                    self.driver.execute_script("arguments[0].click();", food_button)
                    sleep(1)

                    # Correctly handle lists returned by find_elements
                    item_name_elements = self.driver.find_elements(By.CLASS_NAME, '_heroTitle_1nw6t_2')
                    print(f"item_name_elements: {item_name_elements}")

                    item_description_elements = self.driver.find_elements(By.CLASS_NAME, '_description_1nw6t_10')
                    allergens_elements = self.driver.find_elements(By.CLASS_NAME, '_allergens_19184_15')
                    table_rows = self.driver.find_elements(By.XPATH, '//table//tr')

                    item_name = item_name_elements[0].text if item_name_elements else ""  # Handle empty list
                    print(f"item_name: {item_name}")

                    item_description = item_description_elements[0].text if item_description_elements else ""
                    print(f"item_description: {item_description}")

                    allergens = allergens_elements[0].text if allergens_elements else ""
                    print(f"allergens: {allergens}")

                    for row in table_rows:
                        cells = row.find_elements(By.TAG_NAME, 'td')
                        if len(cells) >= 3:  # Check if there are enough cells
                            nutrient = cells[0].text
                            self.data.append({  # Correct append method
                                'rest_name': 'Wagamama',
                                'collection_date': date.today().strftime("%b-%d-%Y"),
                                'item_name': item_name,
                                'item_description': item_description,
                                'allergens': allergens,
                                nutrient: cells[1].text,
                                nutrient + '_100': cells[2].text,
                            })

                    # ... (Close modal code) ...

                except Exception as e:
                    self.log(f"Error processing food item: {e}")
                    continue  # Skip to the next food item if there's an error
            break

        self.driver.quit()
        for item in self.data:
            yield item