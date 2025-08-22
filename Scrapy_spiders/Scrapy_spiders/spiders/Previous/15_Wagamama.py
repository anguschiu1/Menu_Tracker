import time
import pandas as pd
from datetime import date
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os

driver = webdriver.Chrome()
driver.get('https://www.wagamama.com/menu?category=shareables')
driver.maximize_window()
time.sleep(3)
cookie_btn = WebDriverWait(driver,10).until(EC.presence_of_element_located((By.XPATH , "//button[@id='onetrust-accept-btn-handler']"))).click()

category_buttons = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, '//button[contains(@class, "_menuItemButton_1etan_2")]')))
print(len(category_buttons))
ALL_DATAS = []
for button in category_buttons:
    driver.execute_script("arguments[0].click();", button)
    time.sleep(1)  # Wait for the content to load
    outer_food_uls = driver.find_elements(By.XPATH, "//ul[@class='splide__list']")
    print(len(outer_food_uls))
    for outer_food_ul in outer_food_uls:
        try:
            food_btns = outer_food_ul.find_elements(By.XPATH, './/div[contains(@class, "_bottom_pqbyt_34")]//button[contains(@class, "_customButton_dzbl6_2")]')
            print(len(food_btns))
            for food_btn in food_btns:

                try:
                    WebDriverWait(driver, 5).until(EC.element_to_be_clickable(food_btn))
                    driver.execute_script("arguments[0].click();", food_btn)
                except:
                    NEXT_PAGE = outer_food_ul.find_element(By.XPATH , "./parent::div/following-sibling::div/button[@aria-label='Next slide']")
                    if NEXT_PAGE:
                        NEXT_PAGE.click()
                        WebDriverWait(driver, 5).until(EC.element_to_be_clickable(food_btn))
                        driver.execute_script("arguments[0].click();", food_btn)

                time.sleep(1)  # Wait for modal to open
                item_title = driver.find_element(By.XPATH, "//h1[@class='_heroTitle_1nw6t_2']").text
                if item_title in ALL_DATAS:
                    continue
                ALL_DATAS.append(item_title)
                item_description = driver.find_element(By.CLASS_NAME, '_description_1nw6t_10').text
                plus_button = WebDriverWait(driver,10).until(EC.presence_of_element_located((By.XPATH , "//h3[text()='allergens + nutritional information']/following-sibling::button"))).click()
                # plus_button = driver.find_element(By.XPATH , "//h3[text()='allergens + nutritional information']/following-sibling::button").click()
                table_rows = driver.find_elements(By.XPATH, '//table//tr')
                # allergens = driver.find_element(By.CLASS_NAME, "_allergens_19184_15").text
                allergens = driver.find_element(By.XPATH, "//h2[text()='allergens']/following-sibling::p[1]").text
                html_data = {}
                data = {}
                for row in table_rows[1:]:

                    cells = row.find_elements(By.XPATH, './td')
                    nutrient = cells[0].text
                    if cells:
                        data.update({
                            nutrient+"_serving": cells[1].text,
                            nutrient + '_100': cells[2].text,
                        })

                html_data.update({
                    'rest_name': 'Wagamama',
                    'collection_date': date.today().strftime("%b-%d-%Y"),
                    'item_name': item_title,
                    'item_description': item_description,
                    'allergens': allergens,
                })
                html_data.update(data)
                print(item_title)

                df = pd.DataFrame([html_data])
                if os.path.exists('15_wagamama.csv'):
                    df.to_csv('15_wagamama.csv', header=False, index=False, mode='a')
                else:
                    df.to_csv('15_wagamama.csv', header=True, index=False, mode='a')

                plus_button = WebDriverWait(driver,10).until(EC.presence_of_element_located((By.XPATH , "//h3[text()='allergens + nutritional information']/following-sibling::button"))).click()

                try:
                    close_button = WebDriverWait(driver,10).until(EC.presence_of_element_located((By.XPATH, '//button[@id="close"]')))
                    close_button.click()
                except Exception as e:
                    print(f"Failed to close modal: {e}")
                    continue

        except Exception as e:
            print(f"Error navigating to item details: {e}")
            continue
time.sleep(2)

driver.close()