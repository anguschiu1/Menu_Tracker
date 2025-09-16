import os
from datetime import date
from collections import OrderedDict
from typing import List, Dict

import pandas as pd
import requests
from lxml import html

from define_collection_wave import folder
from helpers import create_folder, headers


REST_NAME = 'Cafe Rouge'
LANDING_URL = 'https://www.caferouge.com/restaurants/Center-Parcs/sherwood/menu'
TEN_KITES_BASE = 'https://menus.tenkites.com/thebigtg/mobilemenuscaferouge02'

# Outputs
path_out = create_folder('82_CafeRouge', folder)
file_json = os.path.join(path_out, 'cafe_rouge_items.json')
file_jsonl = os.path.join(path_out, 'cafe_rouge_items_JSONL.json')
file_csv = os.path.join(path_out, 'cafe_rouge_items.csv')


def get_text(node, xpath_expr: str) -> str:
    try:
        res = node.xpath(xpath_expr)
        if not res:
            return ''
        val = res[0] if isinstance(res, list) else res
        if hasattr(val, 'text_content'):
            return val.text_content().strip()
        return str(val).strip()
    except Exception:
        return ''


def fetch_tree(url: str) -> html.HtmlElement:
    resp = requests.get(url, headers=headers, timeout=20)
    resp.raise_for_status()
    return html.fromstring(resp.text)


def extract_menus_from_tree(tree: html.HtmlElement) -> List[Dict[str, str]]:
    """Extract (name, mguid) pairs from a Ten Kites menu tree."""
    seen = OrderedDict()
    # Primary: option spans with data-menu-identifier
    opts = tree.xpath("//div[contains(@class,'k10-menu-selector__option')]/span")
    for opt in opts:
        mguid = opt.get('data-menu-identifier')
        name = get_text(opt, './span/text()') or get_text(opt, 'normalize-space(.)')
        if mguid and mguid not in seen:
            seen[mguid] = name or 'Menu'
    # Fallback: anchors with mguid in href
    if not seen:
        links = tree.xpath("//a[contains(@href,'mguid=')]/@href")
        for href in links:
            m = re.search(r"mguid=([0-9a-fA-F\-]{36})", href)
            if m:
                guid = m.group(1)
                if guid not in seen:
                    # try to find nearby text
                    label_nodes = tree.xpath(f"//a[contains(@href,'{guid}')]")
                    label = label_nodes[0].text_content().strip() if label_nodes else 'Menu'
                    seen[guid] = label
    return [{'mguid': k, 'name': v} for k, v in seen.items()]


def discover_menus(landing_tree: html.HtmlElement) -> List[Dict[str, str]]:
    """Extract (name, mguid) from landing page, Ten Kites iframe, or base page in order."""
    menus = extract_menus_from_tree(landing_tree)
    if menus:
        print(f"Discovered {len(menus)} menu tabs on landing page")
        return menus
    # Try iframe src containing Ten Kites
    iframe_srcs = landing_tree.xpath("//iframe[contains(@src,'tenkites') or contains(@src,'mobilemenus')]/@src")
    for src in iframe_srcs:
        try:
            tk_tree = fetch_tree(src)
            menus = extract_menus_from_tree(tk_tree)
            if menus:
                print(f"Discovered {len(menus)} menu tabs via iframe")
                return menus
        except Exception:
            continue
    # Fallback: Ten Kites base
    try:
        base_tree = fetch_tree(TEN_KITES_BASE)
        menus = extract_menus_from_tree(base_tree)
        if menus:
            print(f"Discovered {len(menus)} menu tabs on Ten Kites base")
            return menus
    except Exception:
        pass
    print("Discovered 0 menu tabs")
    return []


def parse_tenkites_menu(tk_tree: html.HtmlElement, menu_name: str) -> List[Dict]:
    items: List[Dict] = []
    # Keep a running table index like the Scrapy spider (1-based)
    table_index = 1
    categories = tk_tree.xpath("//section[contains(@class,'k10-course')]")
    for category in categories:
        cat_name = get_text(category, 'normalize-space(.//div[@class="k10-course__name"]/text())')
        item_nodes = category.xpath('.//span[contains(@class,"__name")]')
        for item_node in item_nodes:
            item_name = get_text(item_node, 'normalize-space(./text())')
            item_desc = get_text(item_node, 'normalize-space(./parent::div/div[contains(@class,"__desc")]/text())')
            row = {
                'collection_date': date.today().strftime('%b-%d-%Y'),
                'rest_name': REST_NAME,
                'menu_section': cat_name,
                'item_name': item_name,
                'item_description': item_desc,
                'menu_name': menu_name,
            }
            # Select the corresponding table by 1-based index across the whole page
            table = tk_tree.xpath(f'(//table)[{table_index}]')
            if table:
                rows = table[0].xpath('.//tr[contains(@class, "k10-popover__nutrients-table__tr")]')
                for r in rows:
                    key = get_text(r, 'normalize-space(./td[1]/text())')
                    val = get_text(r, 'normalize-space(./td[2]/text())')
                    if key:
                        row[key] = val
            items.append(row)
            table_index += 1
    return items


def save_outputs(records: List[Dict]):
    df = pd.DataFrame(records)
    df.to_csv(file_csv, index=False)
    df.to_json(file_json, orient='records')
    df.to_json(file_jsonl, orient='records', lines=True)
    print(f"Scraped {len(records)} items.")
    print(f"Saved: {file_json}")
    print(f"Saved: {file_jsonl}")
    print(f"Saved: {file_csv}")


def main():
    print(f"Landing URL: {LANDING_URL}")
    landing_tree = fetch_tree(LANDING_URL)
    menus = discover_menus(landing_tree)
    all_items: List[Dict] = []
    if menus:
        for m in menus:
            mguid = m['mguid']
            menu_name = m['name']
            tk_url = f"{TEN_KITES_BASE}?cl=true&mguid={mguid}&internalrequest=true"
            print(f"Fetching Ten Kites: {tk_url} for menu '{menu_name}'")
            tk_tree = fetch_tree(tk_url)
            items = parse_tenkites_menu(tk_tree, menu_name)
            all_items.extend(items)
    else:
        # As a last resort, try parsing the Ten Kites base page as a single menu
        try:
            base_tree = fetch_tree(TEN_KITES_BASE)
            items = parse_tenkites_menu(base_tree, menu_name='Menu')
            all_items.extend(items)
        except Exception:
            pass

    save_outputs(all_items)


if __name__ == '__main__':
    main()
