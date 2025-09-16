import os
import json
from datetime import date
from typing import Dict, List

import requests
import pandas as pd
from lxml import html

from define_collection_wave import folder
from helpers import create_folder, headers


BASE = 'https://timhortons.co.uk'
START_URL = f'{BASE}/menu'
REST_NAME = 'Tim Hortons'

# Outputs
path_out = create_folder('72_TimHortons', folder)
file_json = os.path.join(path_out, 'timhortons_items.json')
file_csv = os.path.join(path_out, 'timhortons_items.csv')


def fetch(url: str) -> html.HtmlElement:
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return html.fromstring(resp.content)


def get_categories_and_items() -> List[Dict[str, str]]:
    """Return a list of dicts with category, item_name, and item_url."""
    tree = fetch(START_URL)
    blocks = tree.xpath('//div[@class="menu-items box-grid small-up-2 medium-up-3 large-up-4"]')
    results: List[Dict[str, str]] = []
    for block in blocks:
        items = block.xpath('./a')
        if not items:
            continue
        cat_name = (items[0].xpath('./div/@class') or [''])[0].replace('anchor', '')
        for a in items:
            item_name = (a.xpath('./p/text()') or [''])[0]
            href = (a.xpath('./@href') or [''])[0]
            if not href:
                continue
            if href.startswith('/'):
                item_url = BASE + href
            else:
                item_url = BASE + '/' + href
            results.append({'category': cat_name, 'item_name': item_name, 'url': item_url})
    return results


def parse_item(item_url: str, category: str, item_name: str) -> Dict:
    tree = fetch(item_url)
    # Nutrition table is the first table under information_detail
    rows = tree.xpath('//div[@class="information_detail"]//table[1]//tr')
    # Serving size from the row whose header contains 'Serving Size'
    servingsize = None
    for r in rows:
        header = ''.join(r.xpath('.//th//text()')).strip()
        if 'Serving Size' in header:
            servingsize = (r.xpath('.//td/text()') or [''])[0]
            break

    record: Dict = {
        'collection_date': date.today().strftime('%b-%d-%Y'),
        'rest_name': REST_NAME,
        'menu_section': category,
        'menu_id': item_url.split('/')[-1],
        'item_name': item_name,
        'servingsize': servingsize,
        'url': item_url,
    }

    # Remaining rows map headers to either _perserving, _percent depending on values
    # Skip the first two rows (typically headers/serving size), follow original logic
    for r in rows[2:]:
        header = ''.join(r.xpath('.//th//text()')).strip()
        values = [v.strip() for v in r.xpath('.//td/text()') if v and v.strip()]
        if not header:
            continue
        if len(values) == 2:
            record[f'{header}_perserving'] = values[0]
            record[f'{header}_percent'] = values[1]
        elif len(values) == 1:
            if values[0].endswith('%') or '%' in values[0]:
                record[f'{header}_percent'] = values[0]
            else:
                record[f'{header}_perserving'] = values[0]

    return record


def crawl_timh():
    items: List[Dict] = []
    for meta in get_categories_and_items():
        try:
            rec = parse_item(meta['url'], meta['category'], meta['item_name'])
            items.append(rec)
        except Exception as e:
            print(f"Failed to parse item {meta['url']}: {e}")
    return items


def save(items: List[Dict]):
    with open(file_json, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    if items:
        pd.DataFrame(items).to_csv(file_csv, index=False)


if __name__ == '__main__':
    results = crawl_timh()
    print(f'Scraped {len(results)} items.')
    save(results)
    print(f'Saved: {file_json}')
    if os.path.exists(file_csv):
        print(f'Saved: {file_csv}')
