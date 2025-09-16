import os
import json
from datetime import date
from typing import Dict, List

import requests
import pandas as pd
from lxml import html

from define_collection_wave import folder
from helpers import create_folder, headers

BASE_URL = 'https://www.tesco.com/zones/tesco-cafe'
REST_NAME = 'Tesco Cafe'

# Outputs
path_out = create_folder('69_TescoCafe', folder)
file_json = os.path.join(path_out, 'tescocafe_items.json')
file_csv = os.path.join(path_out, 'tescocafe_items.csv')


def fetch(url: str) -> html.HtmlElement:
    """Fetch a URL and return lxml tree."""
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return html.fromstring(resp.content)


def get_category_links() -> List[Dict[str, str]]:
    """Find category links in the 'Browse our menus' section.

    Returns a list of dicts with keys: url, category
    """
    tree = fetch(BASE_URL)
    # Locate the h2 containing 'Browse our menus', then the first following div and anchors beneath
    menus = tree.xpath("//h2[contains(normalize-space(.), 'Browse our menus')]/parent::div/following-sibling::div[1]//a")
    results: List[Dict[str, str]] = []
    for a in menus:
        href = a.get('href') or ''
        # Some links may be relative
        if href.startswith('/'):
            href = f'https://www.tesco.com{href}'
        label = a.get('aria-label') or a.text_content().strip()
        if href:
            results.append({'url': href, 'category': label})
    return results


def parse_category_page(url: str, category_label: str) -> List[Dict]:
    """Parse a category page to extract item cards as per the original spider logic."""
    tree = fetch(url)
    # The original spider targeted a deeply classed grid column; we use a robust contains selector
    # and then grab section children representing items.
    sections = tree.xpath('//div[contains(@class, "beans-grid__column")]//section')
    records: List[Dict] = []

    for sec in sections:
        item_all = sec.get('aria-label') or ''
        if not item_all:
            # some sites put aria-label on inner nodes; fallback to first child
            inner = sec.xpath('.//*[@aria-label][1]/@aria-label')
            item_all = inner[0] if inner else ''
        if not item_all:
            # skip if no aria-label to parse
            continue
        # Mirror original parsing rules
        try:
            desc = ','.join(item_all.split(',')[1:-1])
            item_name_all = item_all.split(',')[0].strip()
            name = item_name_all.split('£')[0]
            # extract kcal tokens
            new_cal_list = [i.strip('.').strip('\n') for i in item_all.split(' ') if 'kcal' in i]
            if len(new_cal_list) > 1:
                new_cal_range = [int(i.replace('kcal','').strip(',').strip('(').strip(')')) for i in new_cal_list]
                new_cal = f"{min(new_cal_range)}-{max(new_cal_range)}kcal"
            else:
                new_cal = new_cal_list[0] if new_cal_list else ''
            if name == 'BLT Baguette':
                new_cal = [i.split('.')[0].replace(' ','') for i in item_all.split(',') if 'kcal' in i]
            if name == 'Tuna':
                name = name + desc
                desc = name
        except Exception:
            # fallbacks
            name = item_all.split(',')[0].strip()
            desc = ''
            new_cal = ''

        record: Dict[str, str] = {
            'collection_date': date.today().strftime('%b-%d-%Y'),
            'rest_name': REST_NAME,
            'menu_section': category_label,
            'item_name': name,
            'item_description': desc,
            'kcal': new_cal,
            'url': url,
        }
        records.append(record)

    return records


def crawl_tescocafe() -> List[Dict]:
    items: List[Dict] = []
    cats = get_category_links()
    if not cats:
        print('No category links found. The site structure may have changed or content is client-rendered.')
        return items
    for cat in cats:
        try:
            records = parse_category_page(cat['url'], cat['category'])
            items.extend(records)
        except Exception as e:
            print(f"Failed to parse category {cat['category']} ({cat['url']}): {e}")
    return items


def save(items: List[Dict]):
    with open(file_json, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    if items:
        pd.DataFrame(items).to_csv(file_csv, index=False)


if __name__ == '__main__':
    items = crawl_tescocafe()
    print(f'Scraped {len(items)} items.')
    save(items)
    print(f'Saved: {file_json}')
    if os.path.exists(file_csv):
        print(f'Saved: {file_csv}')
