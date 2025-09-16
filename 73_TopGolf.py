import os
import json
from datetime import date
from typing import Dict, List

import requests
import pandas as pd
from lxml import html

from define_collection_wave import folder
from helpers import create_folder, headers


BASE = 'https://topgolf.kitchencut.com'
START_URL = f'{BASE}/ecom/menu-ewrft-copy-6613ff9a4db83'
REST_NAME = 'Top Golf'

# Outputs
path_out = create_folder('73_TopGolf', folder)
file_json = os.path.join(path_out, 'topgolf_items.json')
file_csv = os.path.join(path_out, 'topgolf_items.csv')


def fetch(url: str) -> html.HtmlElement:
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return html.fromstring(resp.content)


def parse_page(url: str) -> List[Dict]:
    tree = fetch(url)
    categories = tree.xpath('//div[@class="table-responsive"]')
    items: List[Dict] = []
    for category in categories:
        # Category name
        cat_name = (category.xpath('normalize-space(.//h4/text())') or '')
        # Headers: prefer thead th; fall back to all ths if needed
        header_nodes = category.xpath('.//thead//th[contains(@class,"th")]')
        if not header_nodes:
            header_nodes = category.xpath('.//th[contains(@class,"th")]')
        headers_row = [
            (hn.xpath('normalize-space(string())') or '') for hn in header_nodes
        ]
        rows = category.xpath('.//tr[contains(@class,"jsDish")]')
        for row in rows:
            cell_nodes = row.xpath('./td')
            values_full = [
                (cn.xpath('normalize-space(string())') or '') for cn in cell_nodes
            ]
            # Align values to header count to avoid misalignment
            if headers_row:
                values = values_full[:len(headers_row)]
            else:
                values = values_full
            base = dict(zip(headers_row, values))
            # Build allergens string as in original spider
            allerg_nodes = row.xpath('.//td[contains(@class, "active_allergen")]//a')
            allergen_parts: List[str] = []
            for a in allerg_nodes:
                name = (a.xpath('./@data-original-title') or [''])[0]
                text = (a.xpath('normalize-space(string())') or [''])[0]
                part = f"{text} {name}".strip()
                if part:
                    allergen_parts.append(part)
            allergen_string = ','.join(allergen_parts)

            rec: Dict = {
                'collection_date': date.today().strftime('%b-%d-%Y'),
                'rest_name': REST_NAME,
                'menu_section': cat_name,
                'allergens': allergen_string,
            }
            rec.update(base)
            items.append(rec)
    return items


def save(items: List[Dict]):
    with open(file_json, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    if items:
        pd.DataFrame(items).to_csv(file_csv, index=False)


if __name__ == '__main__':
    results = parse_page(START_URL)
    print(f'Scraped {len(results)} items.')
    save(results)
    print(f'Saved: {file_json}')
    if os.path.exists(file_csv):
        print(f'Saved: {file_csv}')
