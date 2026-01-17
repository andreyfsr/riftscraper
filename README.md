# riftscraper

I built this tool to fetch all Riftbound cards from the Riftcodex API, write a
clean JSON export, and download card images.

## What it does

- Fetches all cards from the `/cards` endpoint (paginated).
- Writes `cards.txt` as valid JSON grouped by set.
- Sorts cards by `riftbound_id` (e.g. `***-001-xxx`, `***-002-xxx`, `***-002a-xxx`).
- Downloads each card image into `cards_png/` using `riftbound_id.png`.
- Skips image downloads that already exist.

## Output format

`cards.txt` is a JSON array of sets:

```
[
  {
    "set_id": "",
    "label": "",
    "cards": [
      {
        "name": "...",
        "riftbound_id": "...",
        "public_code": "...",
        "tcgplayer_id": "...",
        "collector_number": 0,
        "attributes": { "energy": 0, "might": 0, "power": 0 },
        "classification": {
          "type": "...",
          "supertype": ,
          "rarity": "...",
          "domain": ["domain"]
        },
        "text": { "rich": "...", "plain": "..." },
        "set": { "set_id": "", "label": "" },
        "media": {
          "image_url": "...",
          "artist": "...",
          "accessibility_text": "..."
        },
        "tags": [],
        "orientation": "",
        "metadata": {
          "clean_name": "...",
          "alternate_art": ,
          "overnumbered": ,
          "signature": 
        }
      }
    ]
  }
]
```

## How to run

```
python main.py
```

## Credits

Card data is sourced from the Riftcodex API: https://riftcodex.com/docs/riftcodex/get-cards-api-cards-get
