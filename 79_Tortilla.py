import time
import pandas as pd
import json
from datetime import date
from selenium import  webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, StaleElementReferenceException
from selenium.webdriver.common.keys import Keys
from typing import List, Dict
import os

from define_collection_wave import folder
from helpers import create_folder, setup_driver, clean_text

REST_NAME = 'Tortilla'
START_URL = 'https://www.tortilla.co.uk/menu/nutrition-and-allergens'

# Outputs
path_out = create_folder('79_Tortilla', folder)
file_json = os.path.join(path_out, '79_Tortilla_items.json')
file_csv = os.path.join(path_out, '79_Tortilla_items.csv')


def accept_cookies(driver):
    """Accepts cookies if the banner is present."""
    try:
        cookie_button_xpath = (
            "//div[contains(@class,'cookie') or contains(@class,'cookies')]//button"
            "[contains(translate(., 'ACCEPTALLOWAGREE', 'acceptallowagree'), 'accept')"
            " or contains(translate(., 'ACCEPTALLOWAGREE', 'acceptallowagree'), 'allow')"
            " or contains(translate(., 'ACCEPTALLOWAGREE', 'acceptallowagree'), 'agree')]"
        )
        btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, cookie_button_xpath))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
        driver.execute_script("arguments[0].click();", btn)
        print("Accepted cookies.")
        time.sleep(1)  # Wait for banner to disappear
    except TimeoutException:
        print("Cookie banner not found or not clickable.")


def close_item_modal(driver):
    """Closes the currently open item modal."""
    try:
        # Try multiple selectors for the close button
        close_selectors = [
            "//button[contains(@class, 'modal__close')]",
            "//button[contains(@aria-label, 'Close') or contains(., 'Close')]",
            "//div[contains(@class,'modal')]//button[contains(@class,'close')]",
        ]
        closed = False
        for sel in close_selectors:
            try:
                close_btn = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, sel))
                )
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", close_btn)
                driver.execute_script("arguments[0].click();", close_btn)
                closed = True
                break
            except Exception:
                continue

        if not closed:
            # Try clicking overlay
            try:
                overlay = driver.find_element(By.XPATH, "//div[contains(@class,'modal') and (contains(@class,'overlay') or contains(@class,'backdrop'))]")
                driver.execute_script("arguments[0].click();", overlay)
                closed = True
            except Exception:
                pass

        if not closed:
            # Try ESC key
            try:
                driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                closed = True
            except Exception:
                pass

        # Wait for modal to be hidden if we attempted to close
        try:
            WebDriverWait(driver, 5).until(
                EC.invisibility_of_element_located((By.XPATH, "//div[contains(@class, 'modal') and contains(@class,'active')]") )
            )
        except Exception:
            pass

        if closed:
            print("    - Modal closed.")
        else:
            print("    - Could not find or click a modal close control.")
        time.sleep(0.3)
    except Exception as e:
        print(f"    - An error occurred while closing the modal: {e}")


def parse_nutrition_tables(driver, category_text, item_text, size_label):
    """Parses the visible nutrition tables for the current item and size."""
    records = []
    try:
        tables = WebDriverWait(driver, 5).until(
            EC.presence_of_all_elements_located((By.XPATH, "//table[contains(@class,'nutrition__ingredient-table')]"))
        )
        print(f"      - Found {len(tables)} nutrition tables for size '{size_label or 'Default'}'.")

        for table in tables:
            # Prefer thead headers
            header_cells = table.find_elements(By.CSS_SELECTOR, 'thead th')
            headers = [clean_text(h.get_attribute('textContent')) for h in header_cells]

            # Data rows
            data_rows = table.find_elements(By.CSS_SELECTOR, 'tbody tr')
            # Fallback to first tbody row th if thead is absent
            if not headers and data_rows:
                ths = data_rows[0].find_elements(By.TAG_NAME, 'th')
                if ths:
                    headers = [clean_text(h.get_attribute('textContent')) for h in ths]
                    data_rows = data_rows[1:]

            if not headers:
                print("      - Skipping table (no headers found).")
                continue

            for row in data_rows:
                cells = [clean_text(td.get_attribute('textContent')) for td in row.find_elements(By.TAG_NAME, 'td')]
                if len(cells) < len(headers):
                    # align if shorter
                    cells = cells + [''] * (len(headers) - len(cells))
                elif len(cells) > len(headers):
                    cells = cells[:len(headers)]
                row_data = dict(zip(headers, cells))
                record = {
                    'collection_date': date.today().strftime('%b-%d-%Y'),
                    'rest_name': REST_NAME,
                    'category_name': category_text,
                    'item_name': item_text,
                    'size': size_label,
                }
                record.update(row_data)
                records.append(record)
        print(f"      - Parsed {len(records)} ingredient rows.")
        # Optional: reset modal view using the 'Start over' button if present
        try:
            start_over_xpath = "//button[contains(translate(., 'START OVER', 'start over'), 'start over')]"
            start_over_btns = driver.find_elements(By.XPATH, start_over_xpath)
            if start_over_btns:
                btn = start_over_btns[0]
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                try:
                    driver.execute_script("arguments[0].click();", btn)
                except ElementClickInterceptedException:
                    time.sleep(0.3)
                    btn.click()
                print("      - Clicked 'Start over'.")
            else:
                print("      - 'Start over' button not found; continuing.")
        except Exception as e:
            print(f"      - Skipping 'Start over' click due to error: {e}")
    except TimeoutException:
        print("      - Timed out waiting for nutrition tables.")
    except Exception as e:
        print(f"      - Error parsing nutrition tables: {e}")
    return records


def process_item(driver, item_button, category_text):
    """Clicks an item, processes all its sizes, and closes the modal."""
    item_records = []
    try:
        item_text = clean_text(item_button.find_element(By.XPATH, './p').get_attribute('textContent'))
    except StaleElementReferenceException:
        # Re-acquire text via JS fallback
        item_text = clean_text(driver.execute_script("return arguments[0].textContent;", item_button))
    print(f"    -> Processing item: {item_text}")

    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", item_button)
        try:
            driver.execute_script("arguments[0].click();", item_button)
        except ElementClickInterceptedException:
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", item_button)
        time.sleep(0.6) # Wait for modal to open

        # Wait for modal content to be ready
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//table[contains(@class, 'nutrition__ingredient-table')]"))
        )

        # Find size options (radio buttons)
        size_radios = driver.find_elements(By.XPATH, "//div[contains(@class,'radio__indicator')]")

        if not size_radios:
            # No size options, parse the default view
            print("      - No size options found, parsing default table.")
            item_records.extend(parse_nutrition_tables(driver, category_text, item_text, 'Default'))
        else:
            print(f"      - Found {len(size_radios)} sizes to process.")
            for i in range(len(size_radios)):
                # Re-find radios to avoid stale elements
                current_radios = driver.find_elements(By.XPATH, "//div[contains(@class,'radio__indicator')]")
                if i >= len(current_radios):
                    print(f"      - Size radio {i+1} is no longer available, skipping.")
                    continue
                
                radio = current_radios[i]
                size_label = clean_text(radio.find_element(By.XPATH, './following-sibling::span').get_attribute('textContent'))
                print(f"      - Processing size: {size_label}")
                
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", radio)
                try:
                    driver.execute_script("arguments[0].click();", radio)
                except ElementClickInterceptedException:
                    time.sleep(0.3)
                    driver.execute_script("arguments[0].click();", radio)
                time.sleep(0.5) # Wait for table to update

                item_records.extend(parse_nutrition_tables(driver, category_text, item_text, size_label))

    except TimeoutException:
        print(f"    - Timed out waiting for item modal content for '{item_text}'.")
    except Exception as e:
        print(f"    - An error occurred while processing item '{item_text}': {e}")
    finally:
        # Always try to close the modal to continue
        close_item_modal(driver)
    
    return item_records


def scrape_tortilla() -> List[Dict]:
    """Main function to orchestrate the scraping of Tortilla's menu."""
    print("Starting Tortilla scraper...")
    driver = setup_driver()
    all_records = []
    try:
        driver.get(START_URL)
        print(f"Navigated to: {START_URL}")
        
        accept_cookies(driver)

        # Get all category tabs
        category_tabs_xpath = "//ul[contains(@class,'tabs')]//li/button"
        category_tabs = WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.XPATH, category_tabs_xpath))
        )
        cat_count = len(category_tabs)
        print(f"Found {cat_count} categories to process.")

        for i in range(cat_count):
            try:
                # Re-find categories each time to prevent stale elements
                current_category_tabs = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.XPATH, category_tabs_xpath))
                )
                category_button = current_category_tabs[i]
                category_text = clean_text(category_button.get_attribute('textContent'))
                print(f"\n--- Processing Category {i + 1}/{cat_count}: {category_text} ---")

                # Capture a representative item before clicking, to wait for staleness after switching tabs
                prev_items = driver.find_elements(By.XPATH, "//button[contains(@class,'nutrition__product')]")
                prev_first = prev_items[0] if prev_items else None

                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", category_button)
                try:
                    driver.execute_script("arguments[0].click();", category_button)
                except ElementClickInterceptedException:
                    time.sleep(0.5)
                    driver.execute_script("arguments[0].click();", category_button)

                # Wait for previous item to go stale (content swapped), if available
                if prev_first is not None:
                    try:
                        WebDriverWait(driver, 5).until(EC.staleness_of(prev_first))
                    except Exception:
                        pass

                # Get all item buttons for the active category
                item_buttons_xpath = "//button[contains(@class,'nutrition__product')]"
                item_buttons = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.XPATH, item_buttons_xpath))
                )
                print(f"  Found {len(item_buttons)} items in this category.")

                for j in range(len(item_buttons)):
                    try:
                        # Re-find item buttons within the loop
                        current_item_buttons = WebDriverWait(driver, 10).until(
                            EC.presence_of_all_elements_located((By.XPATH, item_buttons_xpath))
                        )
                        if j >= len(current_item_buttons):
                            print(f"    Item {j+1} is no longer available, skipping.")
                            break
                        
                        item_records = process_item(driver, current_item_buttons[j], category_text)
                        all_records.extend(item_records)
                    except Exception as e:
                        print(f"    - Skipping item {j+1} due to error: {e}")
            except Exception as e:
                print(f"  - Skipping category {i + 1} due to error: {e}")

    except Exception as e:
        print(f"\nAn unexpected error occurred during the main scrape loop: {e}")
    finally:
        print("\nScraping finished. Closing driver.")
        driver.quit()
        return all_records


def save_records(records: List[Dict]):
    """Saves the scraped records to JSON and CSV files."""
    print(f"\nScraping complete. Found {len(records)} total ingredient records.")
    if not records:
        print("No data to save.")
        # Create empty files for consistency
        with open(file_json, 'w') as f:
            json.dump([], f)
        open(file_csv, 'w').close()
        return

    print(f"Saving data to {file_csv}")
    print(f"Saving data to {file_json}")
    try:
        df = pd.DataFrame(records)
        # Standardize column names
        df.columns = [clean_text(col).replace(' ', '_').lower() for col in df.columns]
        df.to_csv(file_csv, index=False, encoding='utf-8')
        
        # Convert to JSON records for the json file
        records_for_json = df.to_dict(orient='records')
        with open(file_json, 'w', encoding='utf-8') as f:
            json.dump(records_for_json, f, indent=2, ensure_ascii=False)
        
        print(f"Successfully saved data.")
    except Exception as e:
        print(f"An error occurred during file saving: {e}")


if __name__ == '__main__':
    scraped_records = scrape_tortilla()
    save_records(scraped_records)
