# First commit: Riftcodex card export + images

## What I did

- Added a full card fetcher with pagination using the Riftcodex `/cards` API.
- Exported `cards.txt` as valid JSON grouped by set.
- Ensured cards are sorted by `riftbound_id` ordering rules.
- Downloaded card images into `cards_png/` and skip existing files.
- Added logging so I can follow progress during long runs.
- Updated the README with usage, output format, and API credit.

## How I tested

- `python main.py`
