import json
import os
from datetime import date
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup
import pandas as pd

from define_collection_wave import folder
from helpers import create_folder

BASE_START = 'https://www.itsu.com/menu'
BASE_HOST = 'https://www.itsu.com'
REST_NAME = 'Itsu'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
}

# Outputs
path_out = create_folder('38_Itsu', folder)
file_json = os.path.join(path_out, 'itsu_items.json')
file_csv = os.path.join(path_out, 'itsu_items.csv')


def fetch(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.text


def text(node) -> Optional[str]:
    if not node:
        return None
    t = node.get_text(strip=True)
    return t if t else None


def parse_menu_page(html: str) -> List[str]:
    soup = BeautifulSoup(html, 'html.parser')
    links = []
    for a in soup.select('div.item.col-md-4.col-6 a[href]'):
        href = a.get('href')
        if not href:
            continue
        if href.startswith('http'):
            links.append(href)
        else:
            links.append(BASE_HOST + href)
    # de-duplicate while preserving order
    seen = set()
    deduped = []
    for u in links:
        if u not in seen:
            seen.add(u)
            deduped.append(u)
    return deduped


def parse_item_page(html: str) -> Dict:
    soup = BeautifulSoup(html, 'html.parser')

    item_name = text(soup.select_one('h1.h2.secondary-name'))
    item_description = text(soup.select_one('p.description'))

    nutrient_dict: Dict[str, Optional[str]] = {}
    for block in soup.select('dl.nutrition-facts.grid div'):
        title = text(block.select_one('dt.fact-title'))
        value = text(block.select_one('dd.fact-description'))
        if title:
            nutrient_dict[title] = value

    record: Dict = {
        'item_name': item_name,
        'item_description': item_description,
        'rest_name': REST_NAME,
        'collection_date': date.today().strftime('%b-%d-%Y'),
    }
    record.update(nutrient_dict)
    return record


def crawl_itsu():
    start_html = fetch(BASE_START)
    links = parse_menu_page(start_html)
    print(f'Found {len(links)} product links')

    records: List[Dict] = []
    for i, url in enumerate(links, 1):
        try:
            html = fetch(url)
            record = parse_item_page(html)
            records.append(record)
            if i % 25 == 0:
                print(f'  Parsed {i}/{len(links)} items')
        except Exception as e:
            print(f'  Failed to parse {url}: {e}')

    with open(file_json, 'w') as f:
        json.dump(records, f, indent=2)
    try:
        pd.DataFrame(records).to_csv(file_csv, index=False)
    except Exception as e:
        print(f'CSV export failed: {e}')

    print(f'Scraped {len(records)} items.')
    print(f'Saved: {file_json}')
    print(f'Saved: {file_csv}')


if __name__ == '__main__':
    crawl_itsu()
