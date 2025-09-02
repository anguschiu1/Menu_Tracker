# Newer version aims to replace dependency on Scrapy framework
import json
from datetime import date
from time import sleep
import pandas as pd

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from define_collection_wave import folder
from helpers import create_folder, setup_driver, clean_text

path_wagamama = create_folder('15_Wagamama', folder)
file_wagamama_json = path_wagamama + '/wagamama_nutrition.json'
file_wagamama_csv = path_wagamama + '/wagamama_nutrition.csv'


def extract_item_data(driver, food_button, item_index, total_items):
    """Extract data from a single menu item"""
    print(f"  Processing item {item_index + 1}/{total_items}")
    
    try:
        # Wait for button to be clickable and click
        print(f"    Clicking on item button: {food_button.text}")
        WebDriverWait(driver, 1).until(EC.element_to_be_clickable(food_button))
        driver.execute_script("arguments[0].click();", food_button)
        sleep(0.5)
        
        # Extract item data
        item_name = clean_text(driver.find_element(By.CLASS_NAME, '_heroTitle_1nw6t_2').text)
        item_description = clean_text(driver.find_element(By.CLASS_NAME, '_description_1nw6t_10').text)
        allergen_elements = driver.find_elements(By.CLASS_NAME, '_allergens_19184_15')
        # Extract allergens from innerHTML since text is empty
        allergens = ', '.join([clean_text(elem.get_attribute('innerHTML')) 
                              for elem in allergen_elements 
                              if elem.get_attribute('innerHTML') and elem.get_attribute('innerHTML').strip()])
        # Extract nutrition data from table
        try:
            table_rows = driver.find_elements(By.XPATH, '//table//tr')
            if not table_rows:
                table_rows = driver.find_elements(By.XPATH, '//tbody//tr | //div[contains(@class, "nutrition")]//tr')
            
            # Create single item record with all nutrition data
            item_record = {
                'rest_name': 'Wagamama',
                'collection_date': date.today().strftime("%b-%d-%Y"),
                'item_name': item_name,
                'item_description': item_description,
                'allergens': allergens,
            }
            
            # Add nutrition data as fields to the single record
            nutrition_count = 0
            for row in table_rows:
                cells = row.find_elements(By.TAG_NAME, 'td')
                if len(cells) >= 3:
                    nutrient = clean_text(cells[0].get_attribute('innerHTML'))
                    per_serving = clean_text(cells[1].get_attribute('innerHTML'))
                    per_100g = clean_text(cells[2].get_attribute('innerHTML'))

                    if nutrient:
                        item_record[nutrient] = per_serving
                        item_record[nutrient + '_100g'] = per_100g
                        nutrition_count += 1
            
            print(f"    Processed: {item_name} ({nutrition_count} nutrients)")
            nutrition_items = [item_record] if item_record.get('item_name') != 'Unknown' else []
            
        except Exception as e:
            print(f"    Could not extract nutrition data: {str(e)}")
            nutrition_items = []
        
        close_modal(driver)
        return nutrition_items
        
    except Exception as e:
        print(f"    Error processing food item {item_index + 1}: {str(e)}")
        close_modal(driver)
        return []


def close_modal(driver):
    """Close any open modal/popup"""
    try:
        close_buttons = driver.find_elements(By.XPATH, '//a[@class="close"] | //button[contains(@class, "close") or contains(@aria-label, "close")]')
        if close_buttons:
            driver.execute_script("arguments[0].click();", close_buttons[0])
        else:
            from selenium.webdriver.common.keys import Keys
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
        sleep(0.5)
    except:
        pass


def process_category(driver, category_button, cat_index, total_categories):
    """Process all items in a category"""
    print(f"Processing category {cat_index + 1}/{total_categories}")
    
    try:
        # Print the category name
        print(f"Processing category: {category_button.text}")
        # Click on category button
        driver.execute_script("arguments[0].click();", category_button)
        sleep(0.5)
        
        # Get initial count of food items
        all_food_buttons = driver.find_elements(By.XPATH, '//button[contains(@class, "_customButton_4ufhn_2 _customButtonHover_4ufhn_34")]')
        # Filter to only displayed buttons
        food_buttons = [btn for btn in all_food_buttons if btn.is_displayed()]
        total_items = len(food_buttons)
        print(f"Found {total_items} displayed items in category '{category_button.text}' (out of {len(all_food_buttons)} total)")
        
        results = []
        
        # Process each item by index instead of stored elements
        for food_idx in range(total_items):
            try:
                # Refind all food buttons each time and filter for displayed ones
                all_current_buttons = driver.find_elements(By.XPATH, '//button[contains(@class, "_customButton_4ufhn_2 _customButtonHover_4ufhn_34")]')
                current_food_buttons = [btn for btn in all_current_buttons if btn.is_displayed()]
                
                if food_idx < len(current_food_buttons):
                    nutrition_items = extract_item_data(driver, current_food_buttons[food_idx], food_idx, total_items)
                    results.extend(nutrition_items)
                else:
                    print(f"    Item {food_idx + 1} no longer exists, skipping")
                    
            except Exception as e:
                print(f"    Error processing item {food_idx + 1}: {str(e)}")
                continue
        
        return results
        
    except Exception as e:
        print(f"Error processing category {cat_index + 1}: {str(e)}")
        return []


def crawl_wagamama_nutrition():
    # Setup driver using helper function
    driver = setup_driver()
    
    try:
        driver.get("https://www.wagamama.com/menu?category=sides-sharing")
        print("Page URL:", driver.current_url)
        print("Page source length:", len(driver.page_source))
        
        # Wait for page to load
        print("Waiting for page to load...")
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        print("Page loaded.")
        # Handle cookie consent if present, but don't block if absent/un-clickable
        try:
            consent_btn = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.ID, 'onetrust-accept-btn-handler'))
            )
            try:
                WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.ID, 'onetrust-accept-btn-handler')))
                consent_btn.click()
                print("Cookie consent accepted")
                sleep(0.3)
            except Exception:
                try:
                    driver.execute_script("arguments[0].click();", consent_btn)
                    print("Cookie consent accepted via JS")
                    sleep(0.3)
                except Exception:
                    print("Cookie banner present but could not be clicked; continuing without accepting")
        except Exception:
            print("No cookie consent banner; continuing")
        
        # Find all category buttons
        category_buttons = WebDriverWait(driver, 5).until(
            EC.presence_of_all_elements_located((By.XPATH, '//button[contains(@class, "_menuItemButton_1etan_2")]'))
        )
        print(f"Found {len(category_buttons)} categories")
        
        # Process only first category (remove [:1] to process all)
        results = [item for cat_idx, category_button in enumerate(category_buttons)
                  for item in process_category(driver, category_button, cat_idx, len(category_buttons))]
        
        # Save results to JSON file
        with open(file_wagamama_json, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Scraped {len(results)} items. Data saved to {file_wagamama_json}.")
        # Save results to CSV file
        if results:
            df = pd.DataFrame(results)
            df.to_csv(file_wagamama_csv, index=False)
            print(f"Data also saved to CSV: {file_wagamama_csv}")
        else:
            print("No data to save to CSV")

    except Exception as e:
        print(f"Error during scraping: {str(e)}")
    
    finally:
        driver.quit()


if __name__ == "__main__":
    crawl_wagamama_nutrition()
