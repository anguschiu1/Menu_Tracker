import json
import re
from datetime import date
from typing import List, Dict, Any, Optional

import requests
from bs4 import BeautifulSoup  # already in requirements

from define_collection_wave import folder
from helpers import create_folder, PDFDownloader

path_zizzi = create_folder('24_Zizzi', folder)
file_zizzi_json = path_zizzi + '/zizzi_menu.json'

FULL_MENU_URL = 'https://www.zizzi.co.uk/menus/full-menu'
MENUS_FROM_IDS_URL = 'https://www.zizzi.com/wp-json/menus/get_menus_from_ids?ids={ids}'
MENU_FROM_NAME_URL = 'https://www.zizzi.co.uk/wp-json/menus/get_menu_from_name?name={name}'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
}


def fetch(url: str, expect_json: bool = False) -> Any:
    """Helper to GET a URL with basic error handling."""
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json() if expect_json else r.text

def extract_pdf_urls(html: str) -> List[str]:
    """Extract PDF URLs from the menu page HTML."""
    soup = BeautifulSoup(html, 'html.parser')
    pdf_urls = []
    container = soup.find('div', class_='js-menus')
    if not container:
        print('No menu container found for PDF extraction')
        return []
    for data in ['data-allergen', 'data-ingredients', 'data-nutritional']:
        if data:
            # Find all URLs ending with .pdf using regex
            url = container.get(data, '')
            if url:
                pdf_urls.extend(re.findall(r'https?://[^\s"\']+\.pdf', url))
    return pdf_urls
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
    # raw expected like: [6597,6662,...]
    raw = raw.strip().strip('[]')
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
            'rest_name': 'Zizzi',
            'menu_name': menu_name,
            'menu_section': section_title,
            'item_name': item.get('name'),
            'item_id': item.get('id'),
            'kcal': item.get('calorie_information'),
            'item_description': item.get('description'),
            'price': prices.get('core_price_point'),
            'dietary': item.get('dietary')
        }
        records.append(record)
    return records


def crawl_zizzi_menu():
    try:
        print('Fetching full menu page...')
        html = fetch(FULL_MENU_URL)

        # Extract any embedded PDF URLs first and download them (if present)
        pdf_urls = extract_pdf_urls(html)
        if pdf_urls:
            print(f'Found {len(pdf_urls)} PDF URL(s); downloading...')
            for url in pdf_urls:
                print(f'Found PDF URL {url}')
                filepath = path_zizzi + '/' + url.split('/')[-1]
                PDFDownloader(url, filepath)
                print(f'Downloaded PDF to {filepath}')
        else:
            print('No PDF URLs found in page attributes.')

        # The logic below is retained for future use if needed
        # ids = extract_menu_ids(html)
        # print(f'Found {len(ids)} menu id(s)')
        
        # pdf_urls = extract_pdf_urls(html)
        # print(f'Found {len(pdf_urls)} PDF(s)')
        

        # menu_names = fetch_menu_names(ids)
        # print(f'Found {len(menu_names)} menu name(s)')
        # results: List[Dict[str, Any]] = []
        # for name in menu_names:
        #     try:
        #         menu_data = fetch_menu(name)
        #         if not menu_data:
        #             print(f'No data for menu {name}')
        #             continue
        #         section_records = parse_menu_sections(name, menu_data)
        #         print(f"Menu '{name}': {len(section_records)} item(s)")
        #         results.extend(section_records)
        #     except Exception as e:
        #         print(f'Error processing menu {name}: {e}')
        #         continue
        # # Save JSON
        # with open(file_zizzi_json, 'w') as f:
        #     json.dump(results, f, indent=2)
        # print(f'Scraped {len(results)} items. Data saved to {file_zizzi_json}.')
    except Exception as e:
        print(f'Error during Zizzi scraping: {e}')


if __name__ == '__main__':
    crawl_zizzi_menu()
