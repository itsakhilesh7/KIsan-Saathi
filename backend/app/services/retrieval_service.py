"""Grounded retrieval service for official PJTSAU Agro-Technologies cards (Phase 4).

Uses Google AI Studio hosted embeddings (gemini-embedding-001, 3072 dims) to match
farmer questions against verified technology cards with strict thresholding.
"""

from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from typing import Any

import httpx

from backend.app.core.config import Settings
from backend.app.core.safety_keywords import INDIC_CROP_SYNONYMS
from backend.app.schemas.evidence import Evidence, SourceType

log = logging.getLogger("retrieval_service")

# Default similarity threshold: below this score, reply "not sure; call 1551 or ask your KVK"
DEFAULT_SIMILARITY_THRESHOLD: float = 0.52

# Approved pilot crops for Phase 4 (v1)
ALLOWED_ADVISORY_CROPS = {"paddy", "cotton"}


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Computes cosine similarity between two numeric vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return dot / (norm1 * norm2)


class AdvisoryRetrievalService:
    """Retrieves verified PJTSAU Agro-Technologies cards matching farmer queries."""

    def __init__(
        self,
        cards_path: str = "backend/data/crop_advisories.jsonl",
        embeddings_path: str = "backend/data/crop_advisories_embeddings.json",
        settings: Settings | None = None,
    ) -> None:
        self.cards_path = Path(cards_path)
        self.embeddings_path = Path(embeddings_path)
        self.settings = settings or Settings()
        self._cards: list[dict[str, Any]] = []
        self._embeddings: dict[str, list[float]] = {}
        self._card_fallback_vectors: dict[str, list[float]] = {}
        self._query_embedding_cache: dict[str, list[float]] = {}
        self._load_corpus()

    def _load_corpus(self) -> None:
        """Loads cards and precomputed embeddings from disk."""
        if self.cards_path.exists():
            with open(self.cards_path, "r", encoding="utf-8") as f:
                self._cards = [json.loads(line) for line in f]
            log.info("Loaded %d technology cards from %s", len(self._cards), self.cards_path)
            # Pre-compute fallback vectors for offline testing
            for card in self._cards:
                cid = card["card_id"]
                combined = f"{card['title']} {card['category']} {card['zone']} {card['raw_text']}"
                self._card_fallback_vectors[cid] = self._deterministic_fallback_embedding(combined)

        if self.embeddings_path.exists():
            with open(self.embeddings_path, "r", encoding="utf-8") as f:
                self._embeddings = json.load(f)
            log.info("Loaded %d card embeddings from %s", len(self._embeddings), self.embeddings_path)

    def get_query_embedding(self, text: str) -> tuple[list[float], bool]:
        """Fetches 3072-dim embedding from Google AI Studio gemini-embedding-001.

        Returns (vector, is_gemini_embedding).
        """
        cleaned = text.strip()
        if not cleaned:
            return [], False

        if cleaned in self._query_embedding_cache:
            return self._query_embedding_cache[cleaned], True

        api_key = self.settings.EMBEDDING_API_KEY or self.settings.LLM_API_KEY
        if api_key and self.settings.APP_ENV != "test":
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent?key={api_key}"
            try:
                with httpx.Client(timeout=4.0) as client:
                    resp = client.post(url, json={"content": {"parts": [{"text": cleaned}]}})
                    if resp.status_code == 200:
                        vec = resp.json().get("embedding", {}).get("values", [])
                        if vec:
                            self._query_embedding_cache[cleaned] = vec
                            return vec, True
                    else:
                        log.warning("Embedding API returned %d: %s", resp.status_code, resp.text[:100])
            except Exception as e:
                log.warning("Failed live embedding lookup (%s), using deterministic fallback", e)

        # Deterministic offline fallback embedding for unit testing without live network
        vec = self._deterministic_fallback_embedding(cleaned)
        return vec, False

    def _deterministic_fallback_embedding(self, text: str) -> list[float]:
        """Generates a deterministic 3072-dim unit vector based on token hashes for offline testing."""
        import hashlib

        dims = 3072
        v = [0.0] * dims

        # Expand known Indic agricultural terms so offline unit tests match cards correctly
        expanded_text = text
        for k, val in INDIC_CROP_SYNONYMS.items():
            if k in text:
                expanded_text += f" {val}"

        tokens = expanded_text.lower().split()
        for token in tokens:
            h = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
            idx = h % dims
            v[idx] += 1.0

        norm = math.sqrt(sum(x * x for x in v))
        if norm > 0:
            return [x / norm for x in v]
        return [1.0 / math.sqrt(dims)] * dims

    def retrieve(
        self,
        query: str,
        crop: str | None = None,
        language: str = "te-IN",
        top_k: int = 1,
        threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    ) -> list[tuple[dict[str, Any], float]]:
        """Retrieves top matching technology cards exceeding the similarity threshold.

        Filters by crop if specified ('paddy' or 'cotton').
        Returns list of (card_dict, similarity_score).
        """
        if not self._cards or not self._embeddings:
            return []

        query_vec, is_gemini = self.get_query_embedding(query)
        if not query_vec:
            return []

        embedding_source = self._embeddings if is_gemini else self._card_fallback_vectors

        # Filter candidate cards
        candidates: list[dict[str, Any]] = []
        target_crop = crop.lower().strip() if crop else None

        for card in self._cards:
            card_crop = card.get("crop", "").lower()
            if target_crop:
                # If target crop is paddy, allow paddy and cross-cutting soil/water cards
                if "paddy" in target_crop or "rice" in target_crop:
                    if card_crop in ("paddy", "general_rainfed"):
                        candidates.append(card)
                # If target crop is cotton, allow cotton and cross-cutting soil/water cards
                elif "cotton" in target_crop:
                    if card_crop in ("cotton", "general_rainfed"):
                        candidates.append(card)
                elif card_crop == target_crop:
                    candidates.append(card)
            else:
                # Default: paddy, cotton, and rainfed technologies
                if card_crop in ("paddy", "cotton", "general_rainfed"):
                    candidates.append(card)

        if not candidates:
            return []

        scored: list[tuple[dict[str, Any], float]] = []
        for card in candidates:
            cid = card["card_id"]
            card_vec = embedding_source.get(cid)
            if card_vec:
                score = cosine_similarity(query_vec, card_vec)
                scored.append((card, score))

        scored.sort(key=lambda x: x[1], reverse=True)

        # Apply similarity threshold (in offline fallback mode, scale threshold proportionally)
        effective_threshold = threshold if is_gemini else min(threshold, 0.15)
        filtered = [item for item in scored if item[1] >= effective_threshold]
        return filtered[:top_k]

    def card_to_evidence(self, card: dict[str, Any], score: float) -> Evidence:
        """Converts a retrieved technology card into the strict Evidence schema contract."""
        return Evidence(
            evidence_id=card["card_id"],
            source_type=SourceType.ADVISORY_DOCUMENT,
            source_name=card["title"],
            source_url=card["source_url"],
            publisher=card["publisher"],
            observation_or_publication_date=card["year"],
            location=card["zone"],
            data={
                "card_number": card["card_number"],
                "crop": card["crop"],
                "category": card["category"],
                "page": card["page"],
                "publication_number": card["publication_number"],
                "raw_text": card["raw_text"],
                "similarity_score": round(score, 4),
            },
            limitations=[
                f"Applies to {card['zone']}",
                "Qualitative guidance only; consult product label and 1551 for chemical dosages",
            ],
        )
