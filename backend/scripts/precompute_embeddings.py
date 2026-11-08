"""Precomputes and caches 3072-dimensional embeddings for all 35 technology cards."""

from __future__ import annotations

import json
from pathlib import Path

import httpx

from backend.app.core.config import Settings


def precompute():
    s = Settings()
    key = s.LLM_API_KEY
    if not key:
        print("No LLM_API_KEY found.")
        return

    jsonl_path = Path("backend/data/crop_advisories.jsonl")
    if not jsonl_path.exists():
        print("crop_advisories.jsonl does not exist.")
        return

    with open(jsonl_path, "r", encoding="utf-8") as f:
        cards = [json.loads(line) for line in f]

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent?key={key}"
    card_embs = {}
    print(f"Embedding {len(cards)} cards using gemini-embedding-001...")

    with httpx.Client(timeout=30.0) as client:
        for i, card in enumerate(cards):
            text_to_embed = f"{card['title']}. {card['category']}. {card['zone']}. {card['raw_text']}"
            r = client.post(url, json={"content": {"parts": [{"text": text_to_embed}]}})
            if r.status_code == 200:
                emb = r.json().get("embedding", {}).get("values", [])
                card_embs[card["card_id"]] = emb
                print(f"[{i+1}/{len(cards)}] Embedded {card['card_id']} ({len(emb)} dims)")
            else:
                print(f"[{i+1}/{len(cards)}] Error {card['card_id']}: {r.status_code} {r.text[:100]}")

    out_path = Path("backend/data/crop_advisories_embeddings.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(card_embs, f)

    print(f"Successfully saved {len(card_embs)} embeddings to {out_path}")


if __name__ == "__main__":
    precompute()
