import json
import os
import urllib.parse
import urllib.request

BASE_URL = "https://api.riftcodex.com"
CARDS_ENDPOINT = "/cards"
OUTPUT_TXT = "cards.txt"
IMAGES_DIR = "cards_png"


def fetch_json(url: str) -> dict | list:
    print(f"Fetching: {url}")
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "riftscraper/1.0",
        },
    )
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode("utf-8"))


def normalize_next_url(next_value: str) -> str:
    if not next_value:
        return ""
    if next_value.startswith("http://") or next_value.startswith("https://"):
        return next_value
    if not next_value.startswith("/"):
        next_value = f"/{next_value}"
    return f"{BASE_URL}{next_value}"


def extract_cards(payload: dict | list) -> tuple[list, str]:
    if isinstance(payload, list):
        return payload, ""

    if isinstance(payload, dict):
        data = (
            payload.get("items")
            or payload.get("data")
            or payload.get("cards")
            or payload.get("results")
            or []
        )
        next_value = ""
        if "next" in payload:
            next_value = payload.get("next") or ""
        elif "links" in payload and isinstance(payload["links"], dict):
            next_value = payload["links"].get("next") or ""
        return data, normalize_next_url(next_value)

    return [], ""


def format_card(card: dict) -> dict:
    attributes = card.get("attributes") or {}
    classification = card.get("classification") or {}
    text = card.get("text") or {}
    card_set = card.get("set") or {}
    media = card.get("media") or {}
    metadata = card.get("metadata") or {}

    return {
        "name": card.get("name"),
        "riftbound_id": card.get("riftbound_id"),
        "public_code": card.get("public_code"),
        "tcgplayer_id": card.get("tcgplayer_id"),
        "collector_number": card.get("collector_number"),
        "attributes": {
            "energy": attributes.get("energy"),
            "might": attributes.get("might"),
            "power": attributes.get("power"),
        },
        "classification": {
            "type": classification.get("type"),
            "supertype": classification.get("supertype"),
            "rarity": classification.get("rarity"),
            "domain": classification.get("domain") or [],
        },
        "text": {
            "rich": text.get("rich"),
            "plain": text.get("plain"),
        },
        "set": {
            "set_id": card_set.get("set_id"),
            "label": card_set.get("label"),
        },
        "media": {
            "image_url": media.get("image_url"),
            "artist": media.get("artist"),
            "accessibility_text": media.get("accessibility_text"),
        },
        "tags": card.get("tags") or [],
        "orientation": card.get("orientation"),
        "metadata": {
            "clean_name": metadata.get("clean_name"),
            "alternate_art": metadata.get("alternate_art"),
            "overnumbered": metadata.get("overnumbered"),
            "signature": metadata.get("signature"),
        },
    }


def parse_riftbound_id(riftbound_id: str) -> tuple:
    if not riftbound_id:
        return ("", 0, "", "")
    parts = riftbound_id.split("-")
    set_id = parts[0].lower() if parts else ""
    middle = parts[1].lower() if len(parts) > 1 else ""
    rest = parts[2].lower() if len(parts) > 2 else ""

    num_part = 0
    suffix = ""
    current = ""
    for ch in middle:
        if ch.isdigit():
            current += ch
        else:
            suffix += ch
    if current:
        num_part = int(current)

    rest_num = 0
    rest_suffix = ""
    if rest:
        current = ""
        for ch in rest:
            if ch.isdigit():
                current += ch
            else:
                rest_suffix += ch
        if current:
            rest_num = int(current)

    return (set_id, num_part, suffix, rest_num, rest_suffix)


def group_cards_by_set(cards: list[dict]) -> list[dict]:
    grouped: dict[tuple[str, str], list[dict]] = {}
    for card in cards:
        card_set = card.get("set") or {}
        set_id = card_set.get("set_id") or ""
        label = card_set.get("label") or ""
        key = (set_id, label)
        grouped.setdefault(key, []).append(card)

    output: list[dict] = []
    for (set_id, label), set_cards in grouped.items():
        set_cards_sorted = sorted(
            set_cards,
            key=lambda c: parse_riftbound_id(c.get("riftbound_id") or ""),
        )
        output.append(
            {
                "set_id": set_id,
                "label": label,
                "cards": set_cards_sorted,
            }
        )

    output.sort(key=lambda item: item.get("set_id") or "")
    return output


def write_cards_txt(cards: list[dict]) -> None:
    print(f"Writing {len(cards)} cards to {OUTPUT_TXT}")
    output = group_cards_by_set([format_card(card) for card in cards])
    with open(OUTPUT_TXT, "w", encoding="utf-8") as file:
        json.dump(output, file, ensure_ascii=True, indent=2)
        file.write("\n")
    print(f"Finished writing {OUTPUT_TXT}")


def read_existing_cards() -> list[dict]:
    if not os.path.exists(OUTPUT_TXT):
        return []
    try:
        with open(OUTPUT_TXT, "r", encoding="utf-8") as file:
            content = file.read().strip()
            if not content:
                return []
            data = json.loads(content)
            if not isinstance(data, list):
                return []
            if data and isinstance(data[0], dict) and "cards" in data[0]:
                cards: list[dict] = []
                for group in data:
                    if isinstance(group, dict):
                        group_cards = group.get("cards")
                        if isinstance(group_cards, list):
                            cards.extend(group_cards)
                return cards
            return data
    except (json.JSONDecodeError, OSError) as exc:
        print(f"Could not read existing {OUTPUT_TXT}: {exc}")
        return []


def get_png_ids() -> set[str]:
    if not os.path.isdir(IMAGES_DIR):
        return set()
    ids: set[str] = set()
    for filename in os.listdir(IMAGES_DIR):
        if filename.lower().endswith(".png"):
            ids.add(os.path.splitext(filename)[0])
    return ids


def download_images(cards: list[dict]) -> None:
    os.makedirs(IMAGES_DIR, exist_ok=True)
    downloaded = 0
    skipped = 0
    failed = 0
    for card in cards:
        riftbound_id = card.get("riftbound_id")
        media = card.get("media") or {}
        image_url = media.get("image_url")
        if not riftbound_id or not image_url:
            skipped += 1
            continue
        target_path = os.path.join(IMAGES_DIR, f"{riftbound_id}.png")
        if os.path.exists(target_path):
            skipped += 1
            continue
        try:
            print(f"Downloading image for {riftbound_id}")
            urllib.request.urlretrieve(image_url, target_path)
            downloaded += 1
        except Exception as exc:
            failed += 1
            print(f"Failed to download {image_url}: {exc}")
    print(
        f"Images done. Downloaded: {downloaded}, skipped: {skipped}, failed: {failed}"
    )


def fetch_all_cards() -> list[dict]:
    cards: list[dict] = []
    page = 1
    size = 100

    while True:
        print(f"Fetching page {page}")
        query = urllib.parse.urlencode({"page": page, "size": size})
        page_url = f"{BASE_URL}{CARDS_ENDPOINT}?{query}"
        payload = fetch_json(page_url)
        page_cards, _ = extract_cards(payload)
        if page_cards:
            cards.extend(page_cards)
            print(f"Collected {len(page_cards)} cards (total {len(cards)})")
        else:
            print("No cards found on this page.")
        total_pages = payload.get("pages") if isinstance(payload, dict) else None
        if not total_pages or page >= total_pages:
            print("Reached last page.")
            break
        page += 1

    return cards


def main() -> None:
    existing_cards = read_existing_cards()
    existing_ids = {
        card.get("riftbound_id")
        for card in existing_cards
        if isinstance(card, dict)
    }
    existing_ids.discard(None)

    cards = fetch_all_cards()
    cards_by_id = {
        card.get("riftbound_id"): card for card in cards if card.get("riftbound_id")
    }

    png_ids = get_png_ids()
    cards_to_write: list[dict]
    if existing_cards:
        missing_ids = [rid for rid in png_ids if rid not in existing_ids]
        if missing_ids:
            print(f"Filling {len(missing_ids)} missing cards from {IMAGES_DIR}")
        for rid in missing_ids:
            card = cards_by_id.get(rid)
            if card:
                existing_cards.append(format_card(card))
        cards_to_write = existing_cards
    else:
        cards_to_write = [format_card(card) for card in cards]

    write_cards_txt(cards_to_write)
    download_images(cards)
    print(
        f"Wrote {len(cards_to_write)} cards to {OUTPUT_TXT} and images to {IMAGES_DIR}/"
    )


if __name__ == "__main__":
    main()