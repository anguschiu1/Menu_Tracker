# Newer version aims to replace dependency on Scrapy framework
import json
from datetime import date

import google_colab_selenium as gs

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fake_useragent import UserAgent

from define_collection_wave import folder
from helpers import create_folder

path_kfc = create_folder('5_KFC', folder)
file_kfc = path_kfc + '/kfc_nutrition.json'


def crawl_kfc_nutrition():
    # Initialize fake user agent
    ua = UserAgent()
    random_user_agent = ua.random

    options = Options()
    # Add extra options
    options.add_argument("--window-size=1920,1080")  # Set the window size
    options.add_argument("--disable-infobars")  # Disable the infobars
    options.add_argument("--disable-popup-blocking")  # Disable pop-ups
    options.add_argument("--ignore-certificate-errors")  # Ignore certificate errors
    options.add_argument("--incognito")  # Use Chrome in incognito mode

    driver = gs.UndetectedChrome(options=options)

    # Execute script to remove webdriver property
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    try:
        url = "https://www.kfc.co.uk/nutrition-allergens?close"
        driver.get(url)

        # Print page source to see what's actually loaded
        print("Page URL:", driver.current_url)
        print("Page source length:", len(driver.page_source))
        # print("First 1000 characters of page source:")
        print(driver.page_source[:500000])

        # Wait for the script tag to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//script[@id="__NEXT_DATA__"]'))
        )
        text_content = driver.find_element(By.XPATH, '//script[@id="__NEXT_DATA__"]').get_attribute('textContent')
        print("Text content found, length:", len(text_content))
        print("First 200 characters of text content:")
        print(text_content[:200])
        dat = json.loads(text_content)
        items = dat.get('props').get('pageProps').get('data').get('mainContent')[2].get('data').get("children").get("products")
        results = []
        for item in items:
            allergens = item.get('allergens')
            allergen_list = [allergen for allergen in allergens.keys() if allergens.get(allergen).get('type') is not False]
            nutrients = item.get('nutrition')
            vegan = item.get('vegan')
            vegetarian = item.get('vegetarian')
            item_dict = {
                'rest_name': 'KFC',
                'collection_date': date.today().strftime("%b-%d-%Y"),
                'item_name': item.get('name'),
                'menu_section': item.get('categories')[0],
                'allergens': allergen_list,
                'vegan': vegan,
                'vegetarian': vegetarian
            }
            item_dict.update(nutrients)
            results.append(item_dict)
        # Save results to a JSON file
        with open(file_kfc, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Scraped {len(results)} items. Data saved to {file_kfc}.")
    finally:
        driver.quit()

if __name__ == "__main__":
    crawl_kfc_nutrition()
