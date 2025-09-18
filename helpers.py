import json
import os
import re
import subprocess
from ssl import OP_SINGLE_DH_USE
# from tkinter import E
import urllib
from datetime import date
from time import sleep

import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from fake_useragent import UserAgent
from selenium.webdriver.chrome.options import Options

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


from define_collection_wave import folder
import platform

def setup_driver():
    """Setup Chrome driver with anti-detection options"""
    ua = UserAgent()
    random_user_agent = ua.random
    
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument(f"--user-agent={random_user_agent}")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    # Remove webdriver property
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def clean_text(text):
    """Clean text by removing unicode characters and normalizing whitespace"""
    if not text:
        return ""
    # Convert unicode pound sign to proper £ symbol
    cleaned = re.sub(r'\u00a3', '£', text)
    # Remove other problematic unicode characters
    cleaned = re.sub(r'[\u00a0\u2009\u200a\u200b\u2060\ufeff]', ' ', cleaned)
    # Replace multiple whitespace with single space and strip
    cleaned = ' '.join(cleaned.split())
    return cleaned

def setup_driver_colab():
    """Setup Chrome driver with Google Colab specific options"""
    try:
        import google_colab_selenium as gs
    except ImportError:
        raise ImportError("google_colab_selenium is required for Colab environment. Install with: !pip install google_colab_selenium")
    
    from fake_useragent import UserAgent
    from selenium.webdriver.chrome.options import Options
    
    # Initialize fake user agent
    ua = UserAgent()
    random_user_agent = ua.random

    options = Options()
    # Add extra options for Colab environment
    options.add_argument("--window-size=1920,1080")  # Set the window size
    options.add_argument("--disable-infobars")  # Disable the infobars
    options.add_argument("--disable-popup-blocking")  # Disable pop-ups
    options.add_argument("--ignore-certificate-errors")  # Ignore certificate errors
    options.add_argument("--incognito")  # Use Chrome in incognito mode
    options.add_argument(f"--user-agent={random_user_agent}")

    driver = gs.UndetectedChrome(options=options)

    # Execute script to remove webdriver property
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def download_pdf(url, filename, folder_path):
    """Download a PDF file from URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status()
        
        # Ensure filename ends with .pdf
        if not filename.lower().endswith('.pdf'):
            filename += '.pdf'
        
        # Clean filename of invalid characters
        filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
        
        file_path = os.path.join(folder_path, filename)
        
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        
        print(f"Downloaded: {filename}")
        return True
    
    except Exception as e:
        print(f"Error downloading {filename}: {str(e)}")
        return False



# Initialise Selenium web driver
# ua = UserAgent()
# random_user_agent = ua.random

# options = Options()
# options.add_argument('--headless=new')  # Use new headless mode
# options.add_argument('--no-sandbox')
# options.add_argument('--disable-dev-shm-usage')
# options.add_argument(f"--user-agent={random_user_agent}")
# options.add_argument("--disable-blink-features=AutomationControlled")
# options.add_experimental_option("excludeSwitches", ["enable-automation"])
# options.add_experimental_option('useAutomationExtension', False)

# driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# # Execute script to remove webdriver property
# driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

# print(f'header: {random_user_agent}')


# Define paths 
root_path = os.getcwd()
print(f"Root path set to: {root_path}")
# web_browser_path = 'C:\\Users\\angus\\source\\repos\\MenuTracker\\chromedriver.exe'

# windows or osx
if platform.system() == 'Windows':
    # headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'}
    headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Mobile Safari/537.36'}
    operation_system = 'Windows'
else:
    # headers = {'User-Agent': 'Mozilla/5.0 (Linuxintosh; Intel Linux OS X 10_15_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Safari/605.1.15'}
    headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Mobile Safari/537.36'}
    operation_system = 'Linux'


# function to remove html tags
def cleanhtml(raw_html):
    '''
    This function removes html tags from raw html texts
    :param raw_html:
    :return: cleaned text file
    '''
    if not raw_html:
        return raw_html
    else:
        cleanr = re.compile('<.*?>')
        cleantext = re.sub(cleanr, '', raw_html)
        return cleantext

# function to create a folder for each restaurant
def create_folder(rest_name, folder):
    '''
    Creates a folder for each restaurant
    :param rest_name: the name of the restaurant folder
    :return: a new folder for the restaurant will be created
    '''
    rest_folder  =  rest_name + '_' + date.today().strftime("%b-%d-%Y")
    path = os.path.join(folder, rest_folder)
    if not os.path.exists(path):
        os.makedirs(path)
    return path

# function: download a PDF file
def PDFDownloader(url, filePath, verif=True):
    '''
    This function takes in the URL to download a PDF and downloads the PDF file
    :param url: the URL for the PDF
    :param filePath: file path to store the PDF
    :param verif: True or False. Default is set to True. If the PDF download is unsuccessful because of the verification error, set the verif to False
    :return: saves the PDF file
    '''
    r = requests.get(url, stream=True, verify=verif, headers=headers)
    if r.status_code != 200:
        print(f'PDFDownloader: Error {r.status_code} for {url}')
        return
    print(f'PDFDownloader: Downloading PDF for {url}')
    print(f'PDFDownloader: file size {r.headers.get("Content-Length", "unknown")} bytes')
    with open(filePath, "wb") as pdf:
        for chunk in r.iter_content(chunk_size=1024):
            # writing one chunk at a time to a pdf file
            if chunk:
                pdf.write(chunk)

# Downloading multiple PDFs
def combo_PDFDownload(rest_name, url, keyword='pdf', prex=None, verify=True):
    '''
    This function identifies all PDFs available for download and save all of them
    :param rest_name: the name of the restaurant
    :param url: URL for downloading the PDFs
    :param keyword: keyword for identifying the PDF download link. The default is set to 'pdf'
    :param prex: if the PDF download link does not contain domain link, add the domain url here
    :param verify: True or False. whether to allow authentication
    :return: multiple downloaded PDFs
    '''
    path = create_folder(rest_name, folder)
    html = requests.get(url, headers=headers, verify=verify)
    print(f'html: {html}')
    soup = BeautifulSoup(html.text, 'html.parser')
    urls = soup.select(f"a[href*={keyword}]")
    if not urls:
        print(f'No PDF links found for {rest_name} at {url}')
        return
    for url in urls:
        print(url)
        url_link = url.get('href')
        if 'https://' not in url_link and 'http://' not in url_link:
            if url_link[0] != '/':
                url_link = '/' + url_link
            url_link = prex + url_link
        filename = url_link.split('/')[-1]
        if filename[-3:] != 'pdf':
            if '.pdf' in filename: 
                filename = filename.split('?')[0]
            else: 
                filename = filename + '.pdf'
        filename = filename.replace(':', '')
        filename = filename.replace('?','')
        filePath = os.path.join(path,  filename) # path to save the PDF file
        print(url_link)
        print(filePath)
        PDFDownloader(url=url_link, filePath=filePath)
    print('finished downloading pdfs for ' + rest_name)

def combo_PDFDownload_class_name(rest_name, url, keyword='pdf', prex=None, verify=True):
    '''
    This function identifies all PDFs available for download and save all of them
    It finds the links by keywords in the class name instead of href
    :param rest_name: the name of the restaurant
    :param url: URL for downloading the PDFs
    :param keyword: keyword for identifying the PDF download link. The default is set to 'pdf'
    :param prex: if the PDF download link does not contain domain link, add the domain url here
    :param verify: True or False. whether to allow authentication
    :return: multiple downloaded PDFs
    '''
    path = create_folder(rest_name, folder)
    html = requests.get(url, headers=headers, verify=verify)
    soup = BeautifulSoup(html.text, 'html.parser')
    urls = soup.select(f"a[class*={keyword}]")
    filenames = soup.select(f"span[class*={keyword}]")
    for i in range(len(urls)):
        url = urls[i]
        url_link = url.get('href') 
        filename = filenames[i].text + '.pdf'
        filePath = os.path.join(path,  filename)
        print(url_link)
        print(filePath)
        PDFDownloader(url=url_link, filePath=filePath)
    print('finished downloading pdfs for ' + rest_name)

# Download PDFs with Selenium - unified function replacing vue_PDF and java_PDF
def selenium_PDF(rest_name, url, xpath_=None, prefix=None, use_partial_link_text=False, 
                 partial_link_value='Download', navigate_to_links=False, wait_time=5):
    """
    Download PDFs using Selenium with flexible link discovery options.
    
    Args:
        rest_name: Restaurant name for folder creation
        url: Source URL to scrape
        xpath_: XPath selector for finding PDF links (when use_partial_link_text=False)
        prefix: URL prefix to prepend to relative links
        use_partial_link_text: If True, use PARTIAL_LINK_TEXT instead of XPath
        partial_link_value: Text to search for when use_partial_link_text=True
        navigate_to_links: If True, navigate to each link to get final URL
        wait_time: Seconds to wait between operations
    """
    driver = setup_driver()
    
    try:
        print(f'1. Source URL: {url}')
        path = create_folder(rest_name, folder)
        
        print(f'2. Browsing: {url}')
        driver.get(url)
        sleep(wait_time)
        
        # Find PDF links using specified strategy
        if use_partial_link_text:
            print(f'3. Finding links by partial text: {partial_link_value}')
            links = [link.get_attribute('href') for link in
                    driver.find_elements(By.PARTIAL_LINK_TEXT, partial_link_value)]
        else:
            print(f'3. Finding links by XPath: {xpath_}')
            links = [link.get_attribute('href') for link in
                    driver.find_elements(By.XPATH, xpath_)]
        
        print(f'4. Found {len(links)} PDF links')
        
        for i, link in enumerate(links):
            if not link:
                continue
                
            # Navigate to link to get final URL if requested
            if navigate_to_links:
                print(f'5.{i+1} Navigating to: {link}')
                driver.get(link)
                link = driver.current_url
                sleep(wait_time)
            
            # Handle relative URLs
            if prefix and 'https://' not in link and 'http://' not in link:
                if not link.startswith('/'):
                    link = '/' + link
                link = prefix + link
            
            # Process filename
            filename = link.split('/')[-1]
            if not filename.endswith('.pdf'):
                if '.pdf' in filename:
                    filename = filename.split('?')[0]
                else:
                    filename = filename + '.pdf'
            filename = filename.replace(':', '').replace('?', '')
            
            file_path = os.path.join(path, filename)
            print(f'6.{i+1} Downloading: {link} -> {file_path}')
            PDFDownloader(url=link, filePath=file_path)
        
        print(f'7. Finished downloading PDFs for {rest_name}')
        
    finally:
        driver.quit()


# Legacy functions for backward compatibility
def vue_PDF(rest_name, url, xpath_=None):
    """Legacy function - use selenium_PDF instead"""
    return selenium_PDF(rest_name, url, xpath_=xpath_, wait_time=10)


def java_PDF(rest_name, url, prex=None, link_=True, xpath_=None, value='media'):
    """Legacy function - use selenium_PDF instead"""
    return selenium_PDF(
        rest_name=rest_name,
        url=url,
        prefix=prex,
        use_partial_link_text=link_,
        partial_link_value=value if value else 'Download',
        xpath_=xpath_,
        navigate_to_links=True,
        wait_time=5
    )

def IMGDownloader(url, filePath):
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36')]
    urllib.request.install_opener(opener)
    urllib.request.urlretrieve(url, filePath)


def combo_imgDownload(rest_name,url,folder):
    path = create_folder(rest_name, folder)
    # s = Service(web_browser_path)
    # browser = webdriver.Chrome(service=s)
    # browser.get(url)
    driver = setup_driver()
    driver.get(url)

    sleep(10)
    images = driver.find_elements(by=By.XPATH, value='//img[contains(@src, "jpg")]')
    for image in images:
        image_link = image.get_attribute("src")
        print(image_link)
        image_name = image_link.split('/')[-1]
        image_path = os.path.join(path, image_name)
        IMGDownloader(image_link,image_path)


# function: create a folder and run the spider
def RunSpider(spidername, folder, json_=False):
    '''
    This function allows the spiders to run and saves the spider outputs
    :param spidername: the name of the spider you want to run
    :param folder: folder for the data collection wave
    :param json_: Default is False (file saving as csv).
    :return: spider output saved in csv or json
    '''
    #op_sys = platform.system() # for the windows system, I will use the relative path for the file storage path
    #print(op_sys)
    os.chdir(root_path)
    path = create_folder(spidername, folder) # create a folder for the spider output
    os.chdir('./Scrapy_spiders')
    if json_:
        json_file_name = spidername + '_items.json'
        json_file_path_root = os.path.join(root_path, path, json_file_name)
        os.system("scrapy crawl " + spidername + " -o" + json_file_path_root)
        with open(json_file_path_root,'r') as jsonfile:
            json_data = json.load(jsonfile)
            json_df = pd.DataFrame(json_data)
            json_df.to_csv(json_file_path_root.replace('.json', '.csv'), index=False)
    else:
        csv_file_name = spidername + '_items.csv'
        csv_file_path_root = os.path.join(root_path, path, csv_file_name)
        cmd = "scrapy crawl " + spidername + " -o " + csv_file_path_root
        print('cmd=' + cmd)
        # os.system("scrapy crawl " + spidername + " -o " + csv_file_path_root)
    os.chdir(root_path)
    print('root_path=' + root_path)
    print('finished scraping ' + spidername)

# function: run the script for a restaurant (requests)
def RunScript(rest_name):
    try:
        # Use subprocess instead of os.system to capture output
        result = subprocess.run(['python', rest_name + '.py'], 
                              capture_output=True, 
                              text=True)
        
        print(f"=== STDOUT for {rest_name} ===")
        print(result.stdout)
        
        print(f"=== STDERR for {rest_name} ===")
        print(result.stderr)
        
        print(f"=== Return code: {result.returncode} ===")
        
        if result.returncode == 0:
            print('Successfully scraped ' + rest_name)
        else:
            print(f'Issues with {rest_name}. Please Review')
            
    except Exception as e:
        print(f'Exception running {rest_name}: {e}')

# Downloading PDF for Greene King companies
def greene_king_download(rest_name, id, url, folder):
    path = create_folder(rest_name, folder)
    # graphsql 
    request_url ='https://menufinder.greeneking-pubs.co.uk/graphql'
    query_string = "query Menus($venueId: String!) {\n  menus(venueId: $venueId) {\n    id\n    name\n    slug\n    description\n    image\n  }\n}\n"
    payload = {"operationName":"Menus","variables":{"venueId":id},"query":query_string}
    menus = requests.post(request_url, headers = headers, json = payload).json().get('data').get('menus')
    for menu in menus:
        menu_name = menu.get('name')
        print(menu_name + 'Downloading ---->')
        menu_id = menu.get('id')
        # now another post request to get the download link 
        query_string_menu = {"operationName":"MenuPages","variables":{"venueId":id,"menuId":menu_id},"query":"query MenuPages($venueId: String!, $menuId: Int!) {\n  menuPages(venueId: $venueId, menuId: $menuId) {\n    id\n    name\n    downloads {\n      download\n      allergens\n      nutrition\n    }\n    keywords {\n      id\n      name\n      icon\n    }\n    displayGroups {\n      id\n      name\n      groupHeader\n      groupFooter\n      products {\n        id\n        name\n        description\n        new\n        showPrices\n        keywords\n        portions {\n          id\n          name\n          portionName\n          abbreviation\n          price\n        }\n      }\n    }\n  }\n}\n"}
        menu_urls = requests.post(request_url, headers= headers, json = query_string_menu).json().get('data').get('menuPages').get('downloads')
        for value in menu_urls.values():
            if value is not None:
                url_pdf = url + value
                path_temp = os.path.join(path, url_pdf.split('/')[-1]) # path to save the PDF file
                PDFDownloader(url_pdf, path_temp)
