import re
import json
from datetime import date

import requests
import pandas as pd
from bs4 import BeautifulSoup

from define_collection_wave import folder
from helpers import create_folder

# Output paths (match project convention like 14_CaffeNero.py)
path_sizzling = create_folder('18_Sizzling', folder)
file_sizzling_json = path_sizzling + '/sizzling_items.json'
file_sizzling_csv = path_sizzling + '/sizzling_items.csv'

START_URL = 'https://www.smartchef.co.uk/Brands/Suburban'
MENU_URL = 'https://www.smartchef.co.uk/Brands/SuburbanMenuItems?menuid={menuid}'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}


def extract_menu_ids(html):
    """Extract menuid values from the Suburban landing page."""
    soup = BeautifulSoup(html, 'html.parser')
    ids = []
    for a in soup.select('div.hidden-small div ul li a[href]'):
        href = a.get('href', '')
        # href contains a JavaScript call with a quoted id; extract text between single quotes
        matches = re.findall(r"'([^\"]*)'", href)
        if matches:
            ids.append(matches[0])
    return ids


def parse_menu_page(html):
    """Parse a single menu page and return a list of items from that page."""
    soup = BeautifulSoup(html, 'html.parser')

    # Category name from the table preceding the visible-small div (to mirror the Scrapy XPath)
    category = None
    vis_small = soup.select_one('div.visible-small')
    if vis_small:
        table = vis_small.find_previous('table')
        if table:
            span = table.find('span')
            if span:
                category = span.get_text(strip=True)

    items_out = []
    for item in soup.select('div.menuItem'):
        # Nutrients list
        nutrient_spans = [s.get_text(strip=True) for s in item.select('span[style="margin: 6px"]')]
        if nutrient_spans:
            kj = nutrient_spans[0].split('/') [0] if '/' in nutrient_spans[0] else nutrient_spans[0]
            kcal = nutrient_spans[0].split('/') [1] if '/' in nutrient_spans[0] else None
            fat = nutrient_spans[1] if len(nutrient_spans) > 1 else None
            satfat = nutrient_spans[2] if len(nutrient_spans) > 2 else None
            carb = nutrient_spans[3] if len(nutrient_spans) > 3 else None
            sugar = nutrient_spans[4] if len(nutrient_spans) > 4 else None
            protein = nutrient_spans[5] if len(nutrient_spans) > 5 else None
            salt = nutrient_spans[6] if len(nutrient_spans) > 6 else None
        else:
            kj = kcal = fat = satfat = carb = sugar = protein = salt = None

        # Name/description/allergens are in p > span(s)
        name = description = allergens = None
        p = item.find('p')
        if p:
            spans = p.find_all('span')
            if len(spans) > 0:
                name = spans[0].get_text(strip=True)
            if len(spans) > 1:
                description = spans[1].get_text(strip=True)
            if len(spans) > 2:
                allergens = spans[2].get_text(strip=True)

        items_out.append({
            'collection_date': date.today().strftime("%b-%d-%Y"),
            'rest_name': 'Sizzling Pubs',
            'menu_section': category,
            'item_name': name,
            'item_description': description,
            'allergens': allergens,
            'kj': kj,
            'kcal': kcal,
            'fat': fat,
            'satfat': satfat,
            'carb': carb,
            'sugar': sugar,
            'protein': protein,
            'salt': salt,
        })

    return items_out


def main():
    # Fetch landing page
    resp = requests.get(START_URL, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    menu_ids = extract_menu_ids(resp.text)

    results = []
    for menuid in menu_ids:
        url = MENU_URL.format(menuid=menuid)
        r = requests.get(url, headers=HEADERS, timeout=20)
        if r.status_code != 200:
            continue
        results.extend(parse_menu_page(r.text))

    # Save results to CSV and JSON
    if results:
        df = pd.DataFrame(results)
        df.to_csv(file_sizzling_csv, index=False)
        print(f"Scraped {len(results)} items. Data saved to {file_sizzling_csv}.")
        with open(file_sizzling_json, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Scraped {len(results)} items. Data saved to {file_sizzling_json}.")
    else:
        print('No items found to save.')


if __name__ == '__main__':
    main()
