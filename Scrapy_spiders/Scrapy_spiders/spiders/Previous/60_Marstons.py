import time
import pandas as pd
from datetime import date
from selenium import  webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os

driver = webdriver.Chrome()
driver.get('https://www.firestationwaterloo.co.uk/menus')
driver.maximize_window()
time.sleep(3)
cookies_btn = WebDriverWait(driver,10).until(EC.presence_of_element_located((By.XPATH , '//button[@id="ccc-notify-accept"]')))
cookies_btn.click()

all_menus = WebDriverWait(driver,10).until(EC.presence_of_all_elements_located((By.XPATH , "//div[@class='TenKitesMenuBlock_menusList__D_ORl']/button")))

for all_menu in all_menus:
    # all_menu.click()
    driver.execute_script("arguments[0].click();", all_menu)

    menu_name = all_menu.find_element(By.XPATH , "./span").text
    print("Menu Name ----- ----- " , menu_name)

    all_products = driver.find_elements(By.XPATH , '//div[@class="TenKitesMenuBlock_categories__ACeFe"]//h6')

    for all_product in all_products:
        btn = all_product.find_element(By.XPATH , "./ancestor::button[@class='Icons_icon__FC_sy']")
        # btn.click()
        driver.execute_script("arguments[0].click();", btn)
        # print(all_product.text)
        nutrition = {}
        try:
            nutrition_datas = all_product.find_elements(By.XPATH, './following-sibling::div/div')
            if nutrition_datas:
                for nutrition_data in nutrition_datas:
                    nutrition_key = nutrition_data.find_element(By.XPATH, './div[1]').text
                    nutrition_value = nutrition_data.find_element(By.XPATH, './div[2]').text
                    nutrition[nutrition_key] = nutrition_value
        except:
            nutrition_datas = ''
        if nutrition_datas == '':
            continue
        try:
            product_name = all_product.find_element(By.XPATH , './ancestor::div[contains(@class,"Item_item")]/h5').text
        except:
            product_name = ''
        print(product_name)
        try:
            product_description = all_product.find_element(By.XPATH , './ancestor::div[contains(@class,"Item_item")]/p').text.replace('/n',' ').strip()
        except:
            product_description = ''
        try:
            product_price = all_product.find_element(By.XPATH , './ancestor::div[contains(@class,"Item_item")]/div/span').text
        except:
            product_price = ''

        if product_price:
            product_price = product_price[2:]


        data = {
            'collection_date': date.today().strftime("%b-%d-%Y"),
            'rest_name': "Marstons",
            'menu_name' : menu_name,
            'product_name' : product_name,
            'product_description' : product_description,
            'product_price' : product_price,
        }
        data.update(nutrition)

        df = pd.DataFrame([data])
        if os.path.exists('60_Marstons1.csv'):
            df.to_csv('60_Marstons1.csv', header=False, index=False, mode='a')
        else:
            df.to_csv('60_Marstons1.csv', header=True, index=False, mode='a')























    # for all_product in all_products:
    #     nutrition = {}
    #     try:
    #         nutrition_datas = all_product.find_elements(By.XPATH , './following-sibling::div/div')
    #         if nutrition_datas:
    #             for nutrition_data in nutrition_datas:
    #                 nutrition_key = nutrition_data.find_element(By.XPATH , './div[1]').text
    #                 nutrition_value = nutrition_data.find_element(By.XPATH , './div[2]').text
    #                 nutrition[nutrition_key] = nutrition_value
    #     except:
    #         nutrition_datas = ''
    #     if nutrition_datas == '':
    #         continue
    #
    #     try:
    #         product_name = all_product.find_element(By.XPATH , './preceding::div[contains(@class,"Item_item")]/h5').text
    #     except:
    #         product_name = ''
    #     try:
    #         product_description = all_product.find_element(By.XPATH , './preceding::div[contains(@class,"Item_item")]/p').text
    #     except:
    #         product_description = ''
    #     try:
    #         product_name = all_product.find_element(By.XPATH , './preceding::div[contains(@class,"Item_item")]/div/span').text
    #     except:
    #         product_name = ''





    # all_categories = driver.find_elements(By.XPATH , '//div[@class="TenKitesMenuBlock_categories__ACeFe"]/div')
    # for all_category in all_categories:
    #     try:
    #         category_name = all_category.find_element(By.XPATH , './/h2').text
    #     except:
    #         category_name = ''
    #     all_products_category = all_category.find_elements(By.XPATH , './div/div/div/div')
    #     for all_product_category in all_products_category:


driver.close()