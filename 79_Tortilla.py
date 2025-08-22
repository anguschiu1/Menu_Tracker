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

from define_collection_wave import folder
from helpers import create_folder

tortilla_path = create_folder('79_Tortilla', folder)


driver = webdriver.Chrome()
driver.get('https://www.tortilla.co.uk/menu/nutrition-and-allergens')
driver.maximize_window()

cookies_btn = WebDriverWait(driver,10).until(EC.presence_of_element_located((By.XPATH,"//div[@class='cookies__overlay']//button[1]"))).click()




for i in range(0,4):

    for j in range(0,10):
        all_categories = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, f"//ul[@class='tabs']/li[{i + 1}]")))
        category_text = all_categories.find_element(By.XPATH , './button').text
        all_categories.click()
        print(category_text)
        try:
            items = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, "//button[@class='nutrition__product']")))[j]
            item_text = items.find_element(By.XPATH , './p').text
            print(item_text)
        except:
            break
        items.click()

        time.sleep(2)

        radio_indicatores = WebDriverWait(driver,10).until(EC.presence_of_all_elements_located((By.XPATH,"//div[@class='radio__indicator']")))
        for radio_indicatore in radio_indicatores:
            driver.execute_script('window.scrollTo(0, 100);',radio_indicatore)
            radio_indicatore.click()
            table_bodies = WebDriverWait(driver,10).until(EC.presence_of_all_elements_located((By.XPATH , "//table[@class='nutrition__ingredient-table']/tbody")))
            for table_body in table_bodies:
                table_each_row_headings = table_body.find_elements(By.XPATH,'./tr')
                for table_each_row_heading in table_each_row_headings[1:]:
                        heading_row = table_each_row_headings[0].find_elements(By.XPATH , './th')
                        td = []

                        for k in table_each_row_heading.find_elements(By.XPATH,'./td'):
                            try:
                                td.append(k.find_element(By.XPATH,".//span[1]").text)
                            except:
                                td.append(k.text)
                        mix = dict(zip([z.text for z in heading_row],td))
                        data = {
                            'categorie_name' : category_text,
                            'item_name' : item_text,
                            'size' : radio_indicatore.find_element(By.XPATH , './following-sibling::span').text,
                        }
                        data.update(mix)
                        df = pd.DataFrame([data])
                        if os.path.exists(tortilla_path + '/79_Tortilla_items.csv'):
                            df.to_csv(tortilla_path + '/79_Tortilla_items.csv', header=False, index=False, mode='a')
                        else:
                            df.to_csv(tortilla_path + '/79_Tortilla_items.csv', header=True, index=False, mode='a')






        driver.get('https://www.tortilla.co.uk/menu/nutrition-and-allergens')
        time.sleep(2)


# for category in all_categories:
#     category.click()
#     time.sleep(2)
#     element = WebDriverWait(driver,10).until(EC.presence_of_element_located((By.XPATH , "//button[@class='button button--hover-blue u-mt--30']")))
#     # driver.execute_script('arguments[0].click',element)
#     driver.execute_script("arguments[0].scrollIntoView(true);", element)
#     driver.execute_script("arguments[0].scrollIntoView(true);", element)
#     element.click()

driver.quit()
