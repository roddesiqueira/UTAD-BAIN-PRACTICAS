"""Descarga incremental de tweets desde twitter-api45 (RapidAPI).

Replica la logica de DataExtractor.load_data_api del notebook, pero:
- usa solo libreria estandar (el venv .venv_u4 esta roto),
- pagina con next_cursor a traves de varios bloques en una sola ejecucion,
- deduplica por tweet_id contra lo ya guardado para sumar volumen real.
"""

import csv
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
ENV_FILE = HERE / ".env"
OUTPUT = HERE / "data" / "bronze" / "tweets_from_api.csv"
FIELDS = ["user_name", "date", "text", "tweet_id", "user_followers", "is_retweet"]

URL = "https://twitter-api45.p.rapidapi.com/search.php"
HOST = "twitter-api45.p.rapidapi.com"
QUERY = "bitcoin OR btc OR eth OR crypto"
N_BLOCKS = int(sys.argv[1]) if len(sys.argv) > 1 else 8


def load_api_key():
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if line.startswith("RAPIDAPI_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("Falta RAPIDAPI_KEY en .env")


def load_existing_ids():
    if not OUTPUT.exists():
        return set()
    with open(OUTPUT, encoding="utf-8") as f:
        return {row["tweet_id"] for row in csv.DictReader(f)}


def fetch(api_key, cursor=None):
    params = {"query": QUERY, "search_type": "Top"}
    if cursor:
        params["cursor"] = cursor
    req = urllib.request.Request(
        f"{URL}?{urllib.parse.urlencode(params)}",
        headers={"x-rapidapi-host": HOST, "x-rapidapi-key": api_key},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def to_row(t):
    raw_date = t.get("created_at", "")
    try:
        iso = datetime.strptime(raw_date, "%a %b %d %H:%M:%S %z %Y").strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        iso = raw_date
    user_info = t.get("user_info", {}) or {}
    text = t.get("text", "")
    return {
        "user_name": t.get("screen_name", ""),
        "date": iso,
        "text": text,
        "tweet_id": str(t.get("tweet_id", "")),
        "user_followers": user_info.get("followers_count"),
        "is_retweet": str(text).startswith("RT "),
    }


def main():
    api_key = load_api_key()
    seen = load_existing_ids()
    start_count = len(seen)
    print(f"Arranco con {start_count} tweets ya guardados.")

    file_exists = OUTPUT.exists()
    cursor = None
    new_total = 0
    f = open(OUTPUT, "a", newline="", encoding="utf-8")
    writer = csv.DictWriter(f, fieldnames=FIELDS)
    if not file_exists:
        writer.writeheader()

    try:
        for i in range(N_BLOCKS):
            try:
                data = fetch(api_key, cursor)
            except Exception as e:
                print(f"Bloque {i+1}: error de API ({e}). Paro.")
                break
            batch = data.get("timeline", []) or []
            cursor = data.get("next_cursor")
            new_rows = []
            for t in batch:
                row = to_row(t)
                tid = row["tweet_id"]
                if tid and tid not in seen:
                    seen.add(tid)
                    new_rows.append(row)
            if new_rows:
                writer.writerows(new_rows)
                f.flush()
            new_total += len(new_rows)
            print(f"Bloque {i+1}/{N_BLOCKS}: {len(batch)} recibidos, {len(new_rows)} nuevos. Acumulado: {len(seen)}")
            if not cursor:
                print("La API no devolvio mas paginas (sin next_cursor). Paro.")
                break
            time.sleep(1)
    finally:
        f.close()

    print(f"\nFin. Nuevos en esta ejecucion: {new_total}. Total: {start_count} -> {len(seen)}")


if __name__ == "__main__":
    main()
