import os
import re
import json
from datetime import date
from typing import List, Dict

import requests
import pandas as pd
from lxml import html

from define_collection_wave import folder
from helpers import create_folder

BASE_URL = 'https://www.smartchef.co.uk/brands/harvester/'
REST_NAME = 'Harvester'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
}

# Outputs
path_out = create_folder('53_Harvester', folder)
file_json = os.path.join(path_out, 'harvester_items.json')
file_csv = os.path.join(path_out, 'harvester_items.csv')


def fetch(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.text


def parse_menu_ids(html_text: str) -> List[str]:
    sc = html.fromstring(html_text)
    hrefs = sc.xpath('//div[@class="hidden-small"]/div/ul/li/a/@href')
    menu_ids: List[str] = []
    for h in hrefs:
        # The href often contains a quoted menuid inside, e.g., javascript:...('1234')
        m = re.findall(r"'([^\"]*)'", h)
        if m:
            menu_ids.append(m[0])
    return menu_ids


def parse_items_page(html_text: str) -> List[Dict]:
    sc = html.fromstring(html_text)
    # Category appears above items table
    category = sc.xpath('normalize-space(//div[@class="visible-small"]/preceding-sibling::table[1]//span/text())')

    items = sc.xpath('//div[@class="menuItem"]')
    out: List[Dict] = []
    today = date.today().strftime('%b-%d-%Y')

    for it in items:
        # Nutrients listed as spans with style margin:6px
        nutrients = [t.strip() for t in it.xpath('.//span[@style="margin: 6px"]/text()') if t.strip()]
        kj = kcal = fat = satfat = carb = sugar = protein = salt = None
        if nutrients:
            # Defensive parsing: first entry like "1234/567 kcal" or "1234/567"
            first = nutrients[0]
            parts = first.split('/')
            if len(parts) >= 2:
                kj = parts[0].strip()
                kcal = parts[1].strip()
                # Some sites append unit text; normalize e.g., '567 kcal' -> '567'
                kcal = kcal.replace('kcal', '').strip()
            elif len(parts) == 1:
                kj = parts[0].strip()
            # Remaining fields if present in expected order
            def get_or_none(idx: int):
                return nutrients[idx].strip() if len(nutrients) > idx else None
            fat = get_or_none(1)
            satfat = get_or_none(2)
            carb = get_or_none(3)
            sugar = get_or_none(4)
            protein = get_or_none(5)
            salt = get_or_none(6)

        item_name = it.xpath('normalize-space(./p/span[1]/text())')
        item_description = it.xpath('normalize-space(./p/span[2]/text())')
        allergens = it.xpath('normalize-space(./p/span[3]/text())')

        out.append({
            'collection_date': today,
            'rest_name': REST_NAME,
            'menu_section': category or None,
            'item_name': item_name or None,
            'item_description': item_description or None,
            'allergens': allergens or None,
            'kj': kj,
            'kcal': kcal,
            'fat': fat,
            'satfat': satfat,
            'carb': carb,
            'sugar': sugar,
            'protein': protein,
            'salt': salt,
        })
    return out


def crawl_harvester():
    start_html = fetch(BASE_URL)
    menu_ids = parse_menu_ids(start_html)

    all_rows: List[Dict] = []
    for menuid in menu_ids:
        url = f'https://www.smartchef.co.uk/Brands/SuburbanMenuItems?menuid={menuid}'
        try:
            html_text = fetch(url)
            rows = parse_items_page(html_text)
            all_rows.extend(rows)
        except Exception as e:
            print(f'Failed to fetch or parse menuid={menuid}: {e}')

    # Save JSON
    with open(file_json, 'w') as f:
        json.dump(all_rows, f, indent=2)
    # Save CSV
    try:
        pd.DataFrame(all_rows).to_csv(file_csv, index=False)
    except Exception as e:
        print(f'CSV export failed: {e}')

    print(f'Scraped {len(all_rows)} items from {len(menu_ids)} menus.')
    print(f'Saved: {file_json}')
    print(f'Saved: {file_csv}')


if __name__ == '__main__':
    crawl_harvester()
