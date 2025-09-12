import os
from datetime import date
from urllib.parse import urljoin

import pandas as pd
from lxml import html

from define_collection_wave import folder
from helpers import create_folder, setup_driver

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

BASE_URL = 'https://www.benjerry.co.uk/flavours'
HOST = 'https://www.benjerry.co.uk'
REST_NAME = "Ben & Jerry's"

path_benjerry = create_folder('39_BenJerry', folder)


def try_click(driver, xpaths):
    for xp in xpaths:
        try:
            btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, xp))
            )
            btn.click()
            return True
        except Exception:
            continue
    return False


def accept_cookies_if_present(driver):
    xpaths = [
        "//button[contains(., 'Accept')]",
        "//button[contains(., 'I Accept')]",
        "//button[contains(., 'Agree')]",
        "//button[contains(., 'Allow all')]",
        "//button[contains(., 'allow all')]",
    ]
    try_click(driver, xpaths)


def get_text_or_empty(driver, by, selector):
    try:
        return driver.find_element(by, selector).text.strip()
    except NoSuchElementException:
        return ''


def parse_product_page(driver):
    # Ensure title exists
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, 'h1'))
        )
    except TimeoutException:
        pass

    product_name = get_text_or_empty(driver, By.TAG_NAME, 'h1')

    # Description
    try:
        desc_el = driver.find_element(By.XPATH, "//section[@class='flavor-about']/div")
        product_description = desc_el.text.strip()
    except NoSuchElementException:
        product_description = ''

    # Expand Ingredients accordion if needed, then extract text and image
    ingredients = ''
    ingredient_image = ''
    try:
        # Try to click Ingredients button to reveal content
        try_click(driver, ["//button[contains(., 'Ingredients')]"])
        # Now read contents
        try:
            ing_el = driver.find_element(By.XPATH, "//button[contains(., 'Ingredients')]/parent::h3/following-sibling::div")
            ingredients = ing_el.text.replace('Ingredients:', '').strip()
        except NoSuchElementException:
            ingredients = ''
        try:
            img_el = driver.find_element(By.XPATH, "//button[contains(., 'Ingredients')]/parent::h3/following-sibling::div//img")
            src = img_el.get_attribute('src') or ''
            if src:
                ingredient_image = urljoin(HOST + '/', src)
        except NoSuchElementException:
            ingredient_image = ''
    except Exception:
        pass

    return product_name, product_description, ingredients, ingredient_image


def crawl_ben_jerry_selenium():
    driver = setup_driver()
    data_store = []
    try:
        driver.get(BASE_URL)
        accept_cookies_if_present(driver)

        # Wait for category "View All" links
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.XPATH, "//section//a[contains(., 'View All')]"))
            )
        except TimeoutException:
            pass

        cat_links = [a.get_attribute('href') for a in driver.find_elements(By.XPATH, "//section//a[contains(., 'View All')]")]
        cat_links = [l for l in cat_links if l]

        for cat_url in cat_links:
            driver.get(cat_url)
            accept_cookies_if_present(driver)
            # Wait for flavor cards
            try:
                WebDriverWait(driver, 20).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".flavor-card a"))
                )
            except TimeoutException:
                pass

            # Category title
            category_name = get_text_or_empty(driver, By.TAG_NAME, 'h1')

            product_links = [a.get_attribute('href') for a in driver.find_elements(By.CSS_SELECTOR, '.flavor-card a')]
            product_links = [l for l in product_links if l]

            for prod_url in product_links:
                driver.get(prod_url)
                accept_cookies_if_present(driver)
                name, desc, ing, ing_img = parse_product_page(driver)

                record = {
                    'collection_date': date.today().strftime('%b-%d-%Y'),
                    'rest_name': REST_NAME,
                    'category_name': category_name,
                    'product_name': name,
                    'product_description': desc,
                    'ingredients': ing,
                    'ingredient_image': ing_img,
                }
                data_store.append(record)

    finally:
        driver.quit()

    # Write once at end
    df = pd.DataFrame(data_store)
    out_file = os.path.join(path_benjerry, '39_BenJerry_items.csv')
    if os.path.exists(out_file):
        df.to_csv(out_file, header=False, index=False, mode='a')
        print('File appended')
    else:
        df.to_csv(out_file, header=True, index=False, mode='a')
        print('File created')

    print(f"Scraped {len(data_store)} items. Data saved to {out_file}.")


if __name__ == '__main__':
    crawl_ben_jerry_selenium()
