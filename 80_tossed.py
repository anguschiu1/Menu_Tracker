import requests
import json
import pandas as pd
from datetime import date
import os

from define_collection_wave import folder
from helpers import create_folder

# Outputs (mirror MorrisonsCafe structure)
path_out = create_folder('80_Tossed', folder)
file_json = os.path.join(path_out, 'tossed_items.json')
file_jsonl = os.path.join(path_out, 'tossed_items_JSONL.json')
file_csv = os.path.join(path_out, 'tossed_items.csv')


def get_headers() -> dict:
    """Headers required by Tossed VMOS API. Kept explicit to ensure API returns data."""
    return {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'no-store, max-age=0',
        'locale': 'null',
        'menu': '642a94ec-bea1-42a2-8ed1-79225c70aad6',
        'origin': 'https://tosseduk.vmos.io',
        'pragma': 'no-cache',
        'priority': 'u=1, i',
        'referer': 'https://tosseduk.vmos.io/',
        'sec-ch-ua': '"Chromium";v="130", "Not?A_Brand";v="99"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'store': '34412cca-f374-497a-be27-f134e7693c34',
        'tenant': '87a1a7de-18ef-4dcf-b105-45105792347a',
        'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36',
        'x-requested-from': 'online',
    }


def clean_html(text: str) -> str:
    if not isinstance(text, str):
        return ''
    return (
        text.replace('<p>', '')
        .replace('</p>', '')
        .replace('&nbsp;', ' ')
        .replace('&amp;', '&')
        .replace('\n', ' ')
        .replace('<br>', ' ')
        .strip()
    )


def extract_kcal(nutritional: dict) -> int | None:
    """Attempt to extract kcal value from various possible keys."""
    if not isinstance(nutritional, dict):
        return None
    for key in ['kcal', 'Kcal', 'kCal', 'calories', 'Calories', 'energyKcal', 'energy_kcal']:
        if key in nutritional and nutritional[key] not in (None, ''):
            try:
                return int(float(str(nutritional[key]).replace(',', '').strip()))
            except Exception:
                return None
    return None


def fetch_menu_categories(headers: dict) -> list:
    menu_url = 'https://vmos2.vmos.io/catalog/v2/menu'
    resp = requests.get(menu_url, headers=headers)
    data = resp.json()
    return data.get('payload', [{}])[0].get('categories', [])


def fetch_category_bundles(cat_uuid: str, headers: dict) -> dict:
    url = f'https://vmos2.vmos.io/catalog/categories/{cat_uuid}/bundles'
    resp = requests.get(url, headers=headers)
    return resp.json().get('payload', {})


def build_items() -> list[dict]:
    headers = get_headers()
    items: list[dict] = []

    categories = fetch_menu_categories(headers)
    print(f"Found {len(categories)} menu categories")

    for cat in categories:
        cat_uuid = cat.get('uuid')
        menu_name = cat.get('name') or ''
        if not cat_uuid:
            continue
        payload = fetch_category_bundles(cat_uuid, headers)
        categories_payload = payload.get('categories') or []

        bundles_lists = []
        if categories_payload:
            for subcat in categories_payload:
                bundles_lists.append(subcat.get('bundles') or [])
        else:
            bundles_lists.append(payload.get('bundles') or [])

        for bundles in bundles_lists:
            for product in bundles or []:
                product_name = product.get('name', '')
                item_id = product.get('uuid') or product.get('id')
                desc = clean_html(product.get('description', ''))
                # Pull first item variant if present
                first_item = None
                items_list = product.get('items') or []
                if isinstance(items_list, list) and items_list:
                    first_item = items_list[0]
                nutritional = (first_item or {}).get('nutritionalMeta') or {}
                price = (
                    (first_item or {}).get('price')
                    or (first_item or {}).get('basePrice')
                    or product.get('price')
                    or product.get('basePrice')
                )
                kcal = extract_kcal(nutritional)

                row = {
                    'collection_date': date.today().strftime('%b-%d-%Y'),
                    'rest_name': 'Tossed',
                    'menu_section': menu_name,
                    'item_name': product_name,
                    'item_id': item_id,
                    'price': price,
                    'kcal': kcal,
                    'item_description': desc,
                }
                # Also include raw nutritional keys for richness
                if isinstance(nutritional, dict):
                    for k, v in nutritional.items():
                        # don't overwrite canonical kcal if present
                        if k.lower() == 'kcal' and row.get('kcal') is not None:
                            continue
                        row[k] = v
                items.append(row)

    return items


def save_outputs(items: list[dict]):
    df = pd.DataFrame(items)
    df.to_csv(file_csv, index=False)
    df.to_json(file_json, orient='records')
    df.to_json(file_jsonl, orient='records', lines=True)
    print(f"Scraped {len(items)} items.")
    print(f"Saved: {file_json}")
    print(f"Saved: {file_jsonl}")
    print(f"Saved: {file_csv}")


if __name__ == '__main__':
    items = build_items()
    save_outputs(items)