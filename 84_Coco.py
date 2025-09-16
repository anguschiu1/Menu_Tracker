import os
from datetime import date
from typing import List, Dict

import pandas as pd
import requests

from define_collection_wave import folder
from helpers import create_folder, headers


REST_NAME = "Coco Di Mama"
BASE_URL = "https://www.cocodimama.co.uk"
# Menu IDs taken from the original spider
MENU_IDS = [9528, 9530, 9529]
NAMES_URL = f"{BASE_URL}/wp-json/menus/get_menus_from_ids?ids={','.join(map(str, MENU_IDS))}"
MENU_BY_NAME_URL = f"{BASE_URL}/wp-json/menus/get_menu_from_name?name={{name}}"

# Outputs
path_out = create_folder('84_Coco', folder)
file_json = os.path.join(path_out, 'coco_di_mama_items.json')
file_jsonl = os.path.join(path_out, 'coco_di_mama_items_JSONL.json')
file_csv = os.path.join(path_out, 'coco_di_mama_items.csv')


def fetch_json(url: str) -> Dict:
    resp = requests.get(url, headers=headers, timeout=25)
    resp.raise_for_status()
    return resp.json()


def build_records(menu_name: str, payload: Dict) -> List[Dict]:
    records: List[Dict] = []
    data = (payload or {}).get('data') or {}
    sections = data.get('menu_sections') or []

    for section in sections:
        section_title = section.get('section_title') or ''
        items = section.get('items')

        if items is None:
            # Fall back to subsections
            subsections = section.get('subsections') or []
            for subsection in subsections:
                sub_title = subsection.get('title') or section_title
                sub_items = subsection.get('items') or []
                for item in sub_items:
                    price_obj = item.get('prices') or {}
                    # Preserve original spider behavior for subsections
                    price = price_obj.get('london_price_point') or price_obj.get('mid_price_point') or price_obj.get('price') or ''
                    records.append({
                        'collection_date': date.today().strftime('%b-%d-%Y'),
                        'rest_name': REST_NAME,
                        'menu_name': menu_name,
                        'menu_section': sub_title,
                        'item_name': item.get('name'),
                        'item_id': item.get('id'),
                        'kcal': item.get('calorie_information'),
                        'item_description': item.get('description'),
                        'price': price,
                        'dietary': item.get('dietary'),
                    })
        else:
            for item in items or []:
                price_obj = item.get('prices') or {}
                # Preserve original spider behavior for top-level items
                price = price_obj.get('mid_price_point') or price_obj.get('london_price_point') or price_obj.get('price') or ''
                records.append({
                    'collection_date': date.today().strftime('%b-%d-%Y'),
                    'rest_name': REST_NAME,
                    'menu_name': menu_name,
                    'menu_section': section_title,
                    'item_name': item.get('name'),
                    'item_id': item.get('id'),
                    'kcal': item.get('calorie_information'),
                    'item_description': item.get('description'),
                    'price': price,
                    'dietary': item.get('dietary'),
                })
    return records


def save_outputs(records: List[Dict]):
    df = pd.DataFrame(records)
    df.to_csv(file_csv, index=False)
    df.to_json(file_json, orient='records')
    df.to_json(file_jsonl, orient='records', lines=True)
    print(f"Saved {len(df)} items to:\n- {file_json}\n- {file_jsonl}\n- {file_csv}")


def main():
    print(f"[start] Fetching menu names from: {NAMES_URL}")
    names_payload = fetch_json(NAMES_URL)
    menu_names = (names_payload or {}).get('data') or []
    print(f"[info] Found {len(menu_names)} menu name(s)")

    all_records: List[Dict] = []
    for idx, menu in enumerate(menu_names, start=1):
        name = (menu or {}).get('name')
        if not name:
            continue
        url = MENU_BY_NAME_URL.format(name=requests.utils.quote(name))
        print(f"[menu {idx}/{len(menu_names)}] Fetching: {url}")
        try:
            payload = fetch_json(url)
        except Exception as e:
            print(f"[warn] Failed to fetch menu '{name}': {e}")
            continue
        records = build_records(name, payload)
        print(f"[menu {idx}/{len(menu_names)}] Parsed {len(records)} items for '{name}'")
        all_records.extend(records)

    save_outputs(all_records)


if __name__ == '__main__':
    main()
