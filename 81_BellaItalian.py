from datetime import date
import os
import re
import requests
import pandas as pd
from lxml import html

from define_collection_wave import folder
from helpers import create_folder

path_bella = create_folder('81_BellaItalian', folder)


def get_text(node, xpath_expr: str) -> str:
    try:
        res = node.xpath(xpath_expr)
        if not res:
            return ''
        if isinstance(res, list):
            val = res[0]
        else:
            val = res
        if hasattr(val, 'text_content'):
            return val.text_content().strip()
        return str(val).strip()
    except Exception:
        return ''


def parse_menu_page(page_tree, menu_name: str) -> list[dict]:
    items_all: list[dict] = []
    # Sections are nested under //section//section on Ten Kites mobile menus
    menu_sections = page_tree.xpath('//section//section')
    for menu_section in menu_sections:
        menu_section_name = get_text(menu_section, './/div[@class="k10-course__name"]/text()')
        grid_items = menu_section.xpath('.//div[contains(@class, "k10-l-grid__item")]')
        for item in grid_items:
            # Items with BYO recipes
            item_vars = item.xpath('.//div[contains(@class, "k10-byo__item") and contains(@class, "k10-byo-item")]')
            item_description = get_text(item, './/div[@class="k10-byo-item__desc"]/text()')
            has_header = bool(item.xpath('.//div[contains(@class, "k10-byo__header")]'))

            wine_name = ''
            wine_description = ''
            if has_header:
                wine_name = get_text(item, './/div[contains(@class, "k10-byo__header")]//span[@class="k10-byo__name"]/text()')
                wine_description = get_text(item, './/div[contains(@class, "k10-byo__header")]//div[@class="k10-byo__desc"]/text()')

            for item_var in item_vars:
                if has_header:
                    item_name = (wine_name + ' ' + get_text(item_var, './/span[@class="k10-byo-item__name"]/text()')).strip()
                    item_desc = wine_description
                else:
                    item_name = get_text(item_var, './/span[@class="k10-byo-item__name"]/text()')
                    item_desc = item_description

                item_dict = {
                    'rest_name': 'Bella Italia',
                    'collection_date': date.today().strftime('%b-%d-%Y'),
                    'item_name': item_name,
                    'item_description': item_desc,
                    'menu_section': f"{menu_name}, {menu_section_name}" if menu_section_name else menu_name,
                }
                # Nutrition rows: two-column key/value
                nutrition_rows = item_var.xpath('.//table//tr')
                for row in nutrition_rows:
                    key = get_text(row, './td[1]/text()')
                    val = get_text(row, './td[2]/text()')
                    if key:
                        item_dict[key] = val
                items_all.append(item_dict)
    return items_all


def extract_menu_guids(tree) -> list[tuple[str, str]]:
    """Extract (menu_name, guid) tuples from the Ten Kites selector options."""
    pairs: list[tuple[str, str]] = []
    options = tree.xpath('//div[contains(@class, "k10-menu-selector__option")]')
    guid_re = re.compile(r'[0-9a-fA-F\-]{36}')
    for opt in options:
        name = get_text(opt, './/span/text()')
        print(f"menu name: {name}")
        guid = ''
        # common data attrs on Ten Kites
        for attr in ['data-guid', 'data-mguid', 'data-id', 'data-value','data-menu-identifier']:
            val = opt.get(attr)
            if val and guid_re.fullmatch(val.strip()):
                guid = val.strip()
                break
        if not guid:
            # fallback: search in HTML snippet
            snip = html.tostring(opt, encoding='unicode')
            m = guid_re.search(snip)
            if m:
                guid = m.group(0)
        if name and guid:
            pairs.append((name.strip(), guid))
            # print(f"name: {name.strip()}, guid: {guid}")
    return pairs


def main():
    items_all: list[dict] = []
    # Target: Bella Italia Cambridge menu page (embeds Ten Kites)
    landing_url = 'https://www.bellaitalia.co.uk/restaurants/cambridge/leisure-park/menu'
    print(f'url: {landing_url}')
    landing_html = requests.get(landing_url).text
    landing_tree = html.fromstring(landing_html)

    # Try to parse Ten Kites menu options
    menu_pairs = extract_menu_guids(landing_tree)

    # If not found on landing page, try direct Ten Kites base
    if not menu_pairs:
        tk_base = 'https://menus.tenkites.com/thebigtg/mobilemenus03'
        tk_html = requests.get(tk_base).text
        tk_tree = html.fromstring(tk_html)
        menu_pairs = extract_menu_guids(tk_tree)

        # If still nothing, parse whatever is rendered as a single menu
        if not menu_pairs:
            print('No explicit menus found; parsing visible Ten Kites content as a single menu.')
            items_all.extend(parse_menu_page(tk_tree, menu_name='Menu'))
    
    # Iterate menus via mguid if available
    for menu_name, guid in menu_pairs:
        tk_url = f'https://menus.tenkites.com/thebigtg/mobilemenus03?cl=true&mguid={guid}&internalrequest=true'
        tk_resp = requests.get(tk_url)
        tk_tree = html.fromstring(tk_resp.text)
        items_all.extend(parse_menu_page(tk_tree, menu_name=menu_name))

    # Save outputs (CSV to align with original script)
    items_df = pd.DataFrame(items_all)
    out_csv = os.path.join(path_bella, 'bella_items.csv')
    items_df.to_csv(out_csv, index=False)
    print(f'Scraped {len(items_all)} items.')
    print(f'Saved: {out_csv}')


if __name__ == '__main__':
    main()
