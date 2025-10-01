import json
import re
from datetime import date
from typing import List, Dict, Any, Optional

import pandas as pd
import requests
from bs4 import BeautifulSoup  # already in requirements

from define_collection_wave import folder
from helpers import create_folder, PDFDownloader

path_ask = create_folder('25_Ask', folder)
file_ask_json = path_ask + '/ask_menu.json'
file_ask_csv = path_ask + '/ask_menu.csv'

FULL_MENU_URL = 'https://www.askitalian.co.uk/menus/full-menu'
MENUS_FROM_IDS_URL = 'https://www.askitalian.co.uk/wp-json/menus/get_menus_from_ids?ids={ids}'
MENU_FROM_NAME_URL = 'https://www.askitalian.co.uk/wp-json/menus/get_menu_from_name?name={name}'


HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
}

def fetch(url: str, expect_json: bool = False) -> Any:
    """Helper to GET a URL with basic error handling."""
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json() if expect_json else r.text

def find_pdf_urls(html: str) -> Optional[str]:
    """Scan HTML for PDF URLs and download them."""
    try:
        soup = BeautifulSoup(html, 'html.parser')
        target_key = 'ALLERGEN_INFO_LINKS_CONST'
        extracted_lines = []
        pdf_urls = []
        for script in soup.find_all('script'):
            script_text = script.string if script.string else script.get_text()
            if not script_text or target_key not in script_text:
                continue
            for line in script_text.splitlines():
                if target_key in line:
                    clean_line = line.strip()
                    extracted_lines.append(clean_line)
        if extracted_lines:
            print(f'Found {len(extracted_lines)} line(s) containing {target_key}:')
            for line in extracted_lines:
                print(f'  {line}')
                raw_json = re.search(r'ALLERGEN_INFO_LINKS_CONST\s*=\s*`(.*?)`;', line).group(1)
                print(f'Extracted JSON: {raw_json}')
                data = json.loads(raw_json)
                if isinstance(data, list) and data and isinstance(data[0], dict):
                    link = data[0].get('link')
                    if link:
                      pdf_url = link.replace('\\/', '/')
                      print(f'  Found allergen info link: {pdf_url}')
                      pdf_urls.append(pdf_url)
        else:
          print('No script line found containing ALLERGEN_INFO_LINKS_CONST')
        return pdf_urls
    except Exception as se:
          print(f'Error scanning script tags: {se}')

def extract_menu_ids(html: str) -> List[str]:
    """Extract menu IDs from the data-menus attribute of the main container."""
    soup = BeautifulSoup(html, 'html.parser')
    container = soup.find('div', class_='js-menus')
    if not container:
        # Fallback: regex search
        match = re.search(r'data-menus=\"(.*?)\"', html)
        if match:
            raw = match.group(1)
        else:
            return []
    else:
        raw = container.get('data-menus', '')
    # raw expected like: [4182,4448,4632,7102,5430]
    raw = raw.strip().strip('[]')
    print(f'Extracted raw menu IDs: {raw}')
    if not raw:
        return []
    return [part.strip() for part in raw.split(',') if part.strip()]


def fetch_menu_names(ids: List[str]) -> List[str]:
    if not ids:
        return []
    joined = ','.join(ids)
    data = fetch(MENUS_FROM_IDS_URL.format(ids=joined), expect_json=True)
    # data structure: { 'data': [ { 'name': ... }, ... ] }
    menus = data.get('data', []) if isinstance(data, dict) else []
    return [m.get('name') for m in menus if isinstance(m, dict) and m.get('name')]


def fetch_menu(name: str) -> Optional[Dict[str, Any]]:
    if not name:
        return None
    data = fetch(MENU_FROM_NAME_URL.format(name=name), expect_json=True)
    return data.get('data') if isinstance(data, dict) else None


def parse_menu_sections(menu_name: str, menu_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    sections = menu_data.get('menu_sections', []) if menu_data else []
    out: List[Dict[str, Any]] = []
    collection_date = date.today().strftime('%b-%d-%Y')
    for section in sections:
        section_type = section.get('type')
        section_title = section.get('section_title')
        if section_type == 'section':
            items = section.get('items', [])
            out.extend(build_item_records(collection_date, menu_name, section_title, items))
        elif section_type == 'subsections':
            for sub in section.get('subsections', []) or []:
                items = sub.get('items', [])
                out.extend(build_item_records(collection_date, menu_name, section_title, items))
    return out

def build_item_records(collection_date: str, menu_name: str, section_title: str, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        prices = (item.get('prices') or {}) if isinstance(item.get('prices'), dict) else {}
        record = {
            'collection_date': collection_date,
            'rest_name': 'ask',
            'menu_name': menu_name,
            'menu_section': section_title,
            'item_name': item.get('name'),
            'item_id': item.get('id'),
            'kcal': item.get('calorie_information'),
            'item_description': item.get('description'),
            'price': prices.get('mid_price_point'),
            'dietary': item.get('dietary')
        }
        records.append(record)
    return records

def crawl_ask_menu():
  try:
    print('Fetching full menu page...')
    html = fetch(FULL_MENU_URL)

    # Scan <script> nodes for the allergen pdf url
    pdf_urls = find_pdf_urls(html)
    for pdf_url in pdf_urls:
      filepath = path_ask + '/' + pdf_url.split('/')[-1]+'.pdf'
      PDFDownloader(pdf_url, filepath)
      print(f'Downloaded PDF from {pdf_url} to {filepath}...')

    # Extract menu IDs and names, then fetch each menu and parse sections/items
    ids = extract_menu_ids(html)
    print(f'Found {len(ids)} menu id(s)')
    menu_names = fetch_menu_names(ids)
    print(f'Found {len(menu_names)} menu name(s)')
    results: List[Dict[str, Any]] = []
    for name in menu_names:
        try:
            menu_data = fetch_menu(name)
            if not menu_data:
                print(f'No data for menu {name}')
                continue
            section_records = parse_menu_sections(name, menu_data)
            print(f"Menu '{name}': {len(section_records)} item(s)")
            results.extend(section_records)
        except Exception as e:
            print(f'Error processing menu {name}: {e}')
            continue
    
    # Save JSON
    with open(file_ask_json, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Save CSV
    df = pd.DataFrame(results)
    df.to_csv(file_ask_csv, index=False)
    
    print(f'Scraped {len(results)} items.')
    print(f'JSON data saved to {file_ask_json}')
    print(f'CSV data saved to {file_ask_csv}')
  except Exception as e:
      print(f'Error during ask scraping: {e}')


if __name__ == '__main__':
    crawl_ask_menu()
