import json
import os
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from define_collection_wave import folder
from helpers import create_folder, setup_driver, download_pdf

path = create_folder('6_Dominos', folder)

driver = setup_driver()

def scrape_dominos_pdfs():
    """Scrape PDFs from Domino's nutrition page"""
    base_url = "https://corporate.dominos.co.uk/about-us/our-food/allergens-and-nutrition"
    
    driver = setup_driver()
    
    try:
        print(f"Loading page: {base_url}")
        driver.get(base_url)
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        print("Page loaded, searching for PDF links...")
        
        # Find all links that might be PDFs
        links = []
        
        # Method 4: Extract JSON payload used in Next.js SPA
        text_content = driver.find_element(By.XPATH, '//script[@id="__NEXT_DATA__"]').get_attribute('textContent')
        print("Text content found, length:", len(text_content))
        print("First 200 characters of text content:")
        print(text_content[:200])

        dat = json.loads(text_content)
        items = dat.get('props').get('pageProps').get('pageContent').get('mainContent')
        for item in items:
            if item.get('_meta') and item.get('_meta').get('schema') and 'file-download' in item.get('_meta').get('schema') and item.get('link'):
                links.append(item.get('link'))
        links = list(set(links))  # Remove duplicates
        
        # Print all found links for debugging
        print(f"Found {len(links)} potential PDF links")
        for link in links:
            print(f"{link}")
        
        # Download PDFs
        downloaded_count = 0
        for i, link_info in enumerate(links, 1):
            url = link_info
            filename = link_info.split('/')[-1].replace('/', '_').replace('\\', '_') + '.pdf'

            print(f"Attempting to download: {filename}")
            print(f"From: {url}")
            
            if download_pdf(url, filename, path):
                downloaded_count += 1
            
            # Small delay between downloads
            time.sleep(1)
        
        print(f"\nScraping completed!")
        print(f"Downloaded {downloaded_count} files to '{path}' folder")
        
    except Exception as e:
        print(f"Error during scraping: {str(e)}")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_dominos_pdfs()
