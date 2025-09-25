import json
import os
import re
from datetime import date
from typing import Dict, List, Optional, Set, Tuple, Any

import requests
from bs4 import BeautifulSoup
import pandas as pd

from define_collection_wave import folder
from helpers import create_folder


REST_NAME = "YO! Sushi"
# Primary allergen page (grid with tick/M icons); also try a generic tenant path as fallback
BASE_ALLERGEN = "https://menus.tenkites.com/yosushi/allergenpageyosushi"
BASE_TENANT = "https://menus.tenkites.com/yosushi/yosushi"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


# Outputs
path_out = create_folder("28_Yosushi", folder)
file_json = os.path.join(path_out, "yosushi_items.json")
file_csv = os.path.join(path_out, "yosushi_items.csv")


def fetch_html(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.text


def get_menu_guids(home_html: str) -> List[str]:
    """Extract Ten Kites menu GUIDs from the landing page.
    Typical sources:
    - .k10-menu-selector__option[data-menu-identifier]
    - Any element with data-menu-identifier
    - Regex last resort
    """
    soup = BeautifulSoup(home_html, "html.parser")
    guids: List[str] = []

    for node in soup.select(".k10-menu-selector__option[data-menu-identifier]"):
        mguid = node.get("data-menu-identifier")
        if mguid:
            guids.append(mguid.strip())

    if not guids:
        for node in soup.find_all(attrs={"data-menu-identifier": True}):
            mguid = node.get("data-menu-identifier")
            if mguid:
                guids.append(mguid.strip())

    if not guids:
        guids = re.findall(r'data-menu-identifier\s*=\s*"([^"]+)"', home_html)

    # Deduplicate while preserving order
    seen: Set[str] = set()
    uniq: List[str] = []
    for g in guids:
        if g and g not in seen:
            seen.add(g)
            uniq.append(g)
    return uniq


def clean_text(text: Optional[str]) -> Optional[str]:
    if text is None:
        return None
    t = re.sub(r"\s+", " ", text).strip()
    return t if t else None


def sanitize_key(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s


# Canonical allergen and suitability labels we expect in header
CANONICAL_COLS = [
    "Cereals with Gluten",
    "Crustaceans",
    "Eggs",
    "Fish",
    "Peanuts",
    "Soyabeans",
    "Milk",
    "Tree Nuts",
    "Celery",
    "Mustard",
    "Sesame",
    "Sulphur Dioxide / Sulphites",
    "Lupin",
    "Molluscs",
    # Suitability
    "Plant Based",
    "Vegetarians",
]


def map_header_to_cols(header_cells: List[str]) -> Tuple[List[str], Dict[int, str]]:
    """Given header cell texts, build a map of column index -> canonical column name.
    We'll fuzzy-match by normalized keys and also accept partials like 'Sulphur Dioxide'.
    """
    def norm(s: str) -> str:
        return sanitize_key(s.replace("sulfur", "sulphur"))

    canon_norm = {norm(c): c for c in CANONICAL_COLS}

    mapping: Dict[int, str] = {}
    ordered_cols: List[str] = []
    for i, raw in enumerate(header_cells):
        n = norm(raw)
        # Try exact normalized match first
        if n in canon_norm:
            col = canon_norm[n]
        else:
            # Try contains-based heuristics
            if "sulphur" in n or "sulfur" in n:
                col = "Sulphur Dioxide / Sulphites"
            elif "cereal" in n and "gluten" in n:
                col = "Cereals with Gluten"
            elif n in {"vegan", "plant_based", "plant"}:
                col = "Plant Based"
            elif n in {"vegetarian", "vegetarians"}:
                col = "Vegetarians"
            elif n in canon_norm:
                col = canon_norm[n]
            else:
                # Unrecognized; skip
                continue
        mapping[i] = col
        if col not in ordered_cols:
            ordered_cols.append(col)
    return ordered_cols, mapping


def parse_allergen_page(html_text: str) -> List[Dict]:
    """Parse the YO! allergen grid page into item records.
    We expect a table with a header row of allergens and many rows of dishes, grouped by section rows.
    - Tick icon means contains
    - 'M' icon means may contain
    """
    soup = BeautifulSoup(html_text, "html.parser")

    # Locate candidate tables with many headers mentioning allergens
    tables = soup.find_all("table")
    best_table = None
    best_score = -1
    for tbl in tables:
        header_texts = [clean_text(th.get_text(" ", strip=True) or "") or "" for th in tbl.find_all("th")]
        hit = sum(1 for t in header_texts if t and any(k in t.lower() for k in [
            "celery", "crustace", "eggs", "fish", "lupin", "milk", "mollusc", "mustard", "sesame", "soya", "soy", "sulph", "peanut", "tree", "gluten", "plant", "vegetar"
        ]))
        if hit > best_score and hit >= 6:
            best_table = tbl
            best_score = hit

    if best_table is None:
        # Nothing table-like found; return empty
        return []

    # Determine header columns from the first thead row or the first tr with ths
    header_cells: List[str] = []
    thead = best_table.find("thead")
    header_tr = None
    if thead and thead.find("tr"):
        header_tr = thead.find("tr")
    else:
        for tr in best_table.find_all("tr"):
            if tr.find_all("th"):
                header_tr = tr
                break
    if header_tr:
        for th in header_tr.find_all("th"):
            header_cells.append(clean_text(th.get_text(" ", strip=True) or "") or "")

    ordered_cols, idx_to_col = map_header_to_cols(header_cells)

    # Parse body rows; keep track of current section heading rows
    current_section: Optional[str] = None
    records: List[Dict] = []

    def cell_has_icon(td, key: str) -> Tuple[bool, bool]:
        """Return (contains, may_contain) flags for a cell by looking at images/alt/src/text.
        Tick_orange.png => contains
        May_Contain_M_orange.png => may_contain
        Some deployments use 'tick' or 'may' in alt attributes
        """
        contains = False
        may = False
        # Images
        for img in td.find_all("img"):
            src = (img.get("src") or "").lower()
            alt = (img.get("alt") or "").lower()
            if "tick" in src or "tick" in alt:
                contains = True
            if "may_contain" in src or "may" in alt:
                may = True
        # Text fallback: sometimes the letter 'M' is present
        txt = (td.get_text(" ", strip=True) or "").strip().lower()
        if not contains and (txt == "y" or "tick" in txt):
            contains = True
        if not may and (txt == "m" or "may" in txt):
            may = True
        return contains, may

    body_rows = []
    tbody = best_table.find("tbody")
    if tbody:
        body_rows = tbody.find_all("tr")
    else:
        # Fall back to all rows after header
        rows = best_table.find_all("tr")
        if header_tr in rows:
            start = rows.index(header_tr) + 1
            body_rows = rows[start:]
        else:
            body_rows = rows

    for tr in body_rows:
        ths = tr.find_all("th")
        tds = tr.find_all("td")

        # Section row heuristic: a row with a single TH spanning columns or no data cells
        if (len(ths) == 1 and not tds) or (len(ths) == 1 and len(tds) == 0):
            sec = clean_text(ths[0].get_text(" ", strip=True) or "")
            if sec:
                current_section = sec
            continue

        # Item row: expect at least one cell for name plus allergen cells
        cells = ths + tds if ths and tds else (tds or ths)
        if not cells:
            continue
        name = clean_text(cells[0].get_text(" ", strip=True) or "")
        if not name or name.lower() in {"contains/may contain", "contains", "may contain"}:
            continue

        rec: Dict = {
            "collection_date": date.today().strftime("%b-%d-%Y"),
            "rest_name": REST_NAME,
            "menu_section": current_section,
            "item_name": name,
        }

        contains_list: List[str] = []
        may_list: List[str] = []
        suitability: Dict[str, Optional[bool]] = {"Plant Based": None, "Vegetarians": None}

        # Iterate allergen/suitability columns
        for i in range(1, len(cells)):
            if i >= len(header_cells):
                break
            td = cells[i]
            if i not in idx_to_col:
                continue
            col_name = idx_to_col[i]
            cont, may = cell_has_icon(td, col_name)
            if col_name in ("Plant Based", "Vegetarians"):
                # Suitable if tick; treat 'may' as False
                suitability[col_name] = True if cont else False if (not cont and may) else suitability[col_name]
            else:
                if cont:
                    contains_list.append(col_name)
                if may:
                    may_list.append(col_name)

        if contains_list:
            rec["allergens_contains"] = "; ".join(contains_list)
        if may_list:
            rec["allergens_may_contain"] = "; ".join(may_list)
        for k, v in suitability.items():
            if v is not None:
                rec[sanitize_key(k)] = v

        records.append(rec)

    return records


def _json_loads_candidates(raw: str) -> List[Any]:
    """Some Ten Kites pages embed multiple JSON-LD blocks or a top-level array.
    Try to parse as a single object, array of objects, or newline-delimited objects.
    Return a list of JSON objects.
    """
    raw = raw.strip()
    candidates: List[Any] = []
    try:
        obj = json.loads(raw)
        if isinstance(obj, list):
            candidates.extend(obj)
        else:
            candidates.append(obj)
        return candidates
    except Exception:
        pass

    # Try line-delimited
    parts = [p for p in raw.splitlines() if p.strip()]
    for p in parts:
        try:
            candidates.append(json.loads(p))
        except Exception:
            continue
    return candidates


def parse_jsonld_menu(html_text: str) -> List[Dict]:
    """Parse schema.org Menu JSON-LD recursively into records with sections.
    Captures: section trail, item name, description, price, currency, nutrition.
    """
    soup = BeautifulSoup(html_text, "html.parser")
    scripts = soup.find_all("script", attrs={"type": "application/ld+json"})
    if not scripts:
        return []

    def norm_price(price: Optional[str], currency: Optional[str]) -> Optional[str]:
        if not price:
            return None
        p = str(price).strip()
        # Some pages provide numeric strings
        if re.fullmatch(r"\d+(?:[\.,]\d{1,2})?", p):
            p = p.replace(",", ".")
            if currency and currency.upper() == "GBP":
                return f"£{p}"
            return p
        return p

    records: List[Dict] = []

    def walk(node: Any, trail: List[str]):
        if isinstance(node, dict):
            t = (node.get("@type") or node.get("type") or "").lower()
            if t == "menusection":
                name = node.get("name") or node.get("headline")
                sec = clean_text(str(name) if name is not None else None)
                new_trail = trail + ([sec] if sec else [])
                # Traverse both hasMenuSection and hasMenuItem
                for child in node.get("hasMenuSection", []) or []:
                    walk(child, new_trail)
                for mi in node.get("hasMenuItem", []) or []:
                    walk(mi, new_trail)
                return
            if t == "menuitem":
                name = clean_text(node.get("name"))
                if not name:
                    return
                desc = clean_text(node.get("description"))
                offers = node.get("offers") or {}
                if isinstance(offers, list):
                    offers = offers[0] if offers else {}
                price = norm_price(offers.get("price"), offers.get("priceCurrency"))
                nutrition = node.get("nutrition") or {}
                rec: Dict[str, Any] = {
                    "collection_date": date.today().strftime("%b-%d-%Y"),
                    "rest_name": REST_NAME,
                    "menu_section": " > ".join([s for s in trail if s]),
                    "item_name": name,
                    "item_description": desc,
                }
                if price:
                    rec["price"] = price
                # Flatten common nutrition fields if available
                if isinstance(nutrition, dict):
                    for k in [
                        "calories",
                        "carbohydrateContent",
                        "fatContent",
                        "fiberContent",
                        "proteinContent",
                        "saturatedFatContent",
                        "sugarContent",
                        "sodiumContent",
                        "cholesterolContent",
                    ]:
                        v = nutrition.get(k)
                        if v:
                            rec[sanitize_key(k)] = clean_text(str(v))
                records.append(rec)
                return
            # Top-level Menu with hasMenuSection
            if t == "menu":
                for child in node.get("hasMenuSection", []) or []:
                    walk(child, trail)
                return
            # Generic container: traverse children
            for k, v in list(node.items()):
                if isinstance(v, (dict, list)):
                    walk(v, trail)
        elif isinstance(node, list):
            for el in node:
                walk(el, trail)

    for s in scripts:
        raw = s.string or s.text or ""
        if not raw.strip():
            continue
        for obj in _json_loads_candidates(raw):
            walk(obj, [])

    return records


def crawl_yosushi() -> List[Dict]:
    print("Fetching YO! Sushi allergen page...")
    home = fetch_html(BASE_ALLERGEN)
    guids = get_menu_guids(home)
    print(f"Found {len(guids)} menu GUID(s)")

    all_records: List[Dict] = []

    def build_candidates(guid: str) -> List[str]:
        bases = [BASE_ALLERGEN, BASE_TENANT]
        urls: List[str] = []
        for b in bases:
            urls.append(f"{b}?mguid={guid}")
            urls.append(f"{b}?cl=true&mguid={guid}")
            urls.append(f"{b}?internalrequest=true&mguid={guid}")
            urls.append(f"{b}?internalrequest=true&cl=true&mguid={guid}")
        return urls

    if not guids:
        print("No GUIDs found; parsing landing allergen page as single menu")
        # Try JSON-LD first, then allergen grid fallback
        parsed = parse_jsonld_menu(home)
        if not parsed:
            parsed = parse_allergen_page(home)
        all_records.extend(parsed)
        return all_records

    for g in guids:
        parsed_for_guid: List[Dict] = []
        last_html: Optional[str] = None
        for url in build_candidates(g):
            try:
                html_text = fetch_html(url)
                last_html = html_text
                # Prefer JSON-LD
                recs = parse_jsonld_menu(html_text)
                if not recs:
                    recs = parse_allergen_page(html_text)
                if recs:
                    parsed_for_guid = recs
                    print(f" - {len(recs)} row(s) from mguid {g} via {url}")
                    break
            except Exception as e:
                print(f"Failed to fetch mguid {g} via {url}: {e}")
                continue
        if not parsed_for_guid:
            print(f" - 0 row(s) from mguid {g} across candidate URLs")
            # Dump HTML for debugging
            try:
                if last_html:
                    dump_path = os.path.join(path_out, f"debug_mguid_{g[:8]}.html")
                    with open(dump_path, "w") as f:
                        f.write(last_html)
                    print(f"   [debug] saved last fetched HTML to {dump_path}")
            except Exception as e:
                print(f"   [debug] failed to write debug HTML: {e}")
        all_records.extend(parsed_for_guid)

    # Dedupe by section + item name
    seen_pairs: Set[Tuple[Optional[str], str]] = set()
    unique: List[Dict] = []
    for r in all_records:
        key = (r.get("menu_section"), r.get("item_name", ""))
        if key in seen_pairs:
            continue
        seen_pairs.add(key)
        unique.append(r)

    return unique


def save_outputs(items: List[Dict]):
    with open(file_json, "w") as f:
        json.dump(items, f, indent=2)
    try:
        pd.DataFrame(items).to_csv(file_csv, index=False)
    except Exception as e:
        print(f"CSV export failed: {e}")
    print(f"Saved: {file_json}")
    print(f"Saved: {file_csv}")


if __name__ == "__main__":
    data = crawl_yosushi()
    print(f"Total items scraped: {len(data)}")
    save_outputs(data)
