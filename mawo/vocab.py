"""Custom vocabulary for runtime word additions."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class CustomWord:
    """Represents a custom word entry.

    Attributes:
        word: The word
        pos: Part of speech
        gender: Gender (for nouns/adjectives)
        animacy: Animacy (for nouns)
        tags: Additional tags
        paradigm: Paradigm type (for inflection)
    """

    word: str
    pos: str
    gender: str | None = None
    animacy: str | None = None
    tags: dict[str, Any] | None = None
    paradigm: str | None = None


class CustomVocabulary:
    """Custom vocabulary for adding words at runtime.

    Allows adding domain-specific terms without rebuilding DAWG dictionaries.

    Example:
        >>> vocab = CustomVocabulary()
        >>> vocab.add("блокчейн", pos="NOUN", gender="masc")
        >>> vocab.has("блокчейн")
        True
    """

    def __init__(self) -> None:
        """Initialize empty custom vocabulary."""
        self._words: dict[str, CustomWord] = {}
        self._domains: dict[str, list[CustomWord]] = {}

    def add(
        self,
        word: str,
        pos: str,
        gender: str | None = None,
        animacy: str | None = None,
        tags: dict[str, Any] | None = None,
        paradigm: str | None = None,
    ) -> None:
        """Add a word to custom vocabulary.

        Args:
            word: Word to add
            pos: Part of speech (NOUN, VERB, ADJ, etc.)
            gender: Gender (masc/fem/neut) for nouns/adjectives
            animacy: Animacy (anim/inan) for nouns
            tags: Additional tags
            paradigm: Paradigm type for inflection

        Example:
            >>> vocab.add("крипта", pos="NOUN", gender="fem", paradigm="жена")
        """
        self._words[word.lower()] = CustomWord(
            word=word,
            pos=pos,
            gender=gender,
            animacy=animacy,
            tags=tags or {},
            paradigm=paradigm,
        )

    def has(self, word: str) -> bool:
        """Check if word is in custom vocabulary.

        Args:
            word: Word to check

        Returns:
            True if word is in vocabulary
        """
        return word.lower() in self._words

    def get(self, word: str) -> CustomWord | None:
        """Get custom word entry.

        Args:
            word: Word to get

        Returns:
            CustomWord if found, None otherwise
        """
        return self._words.get(word.lower())

    def load(self, file_path: str | Path) -> None:
        """Load vocabulary from file.

        File format (text):
            блокчейн|NOUN|masc|inan
            крипта|NOUN|fem|inan|жена-type
            майнинг|NOUN|masc|inan

        Or JSON:
            [
                {"word": "блокчейн", "pos": "NOUN", "gender": "masc"},
                {"word": "крипта", "pos": "NOUN", "gender": "fem"}
            ]

        Args:
            file_path: Path to vocabulary file
        """
        path = Path(file_path)

        if path.suffix == ".json":
            self._load_json(path)
        else:
            self._load_text(path)

    def _load_json(self, path: Path) -> None:
        """Load vocabulary from JSON file."""
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        for item in data:
            self.add(
                word=item["word"],
                pos=item["pos"],
                gender=item.get("gender"),
                animacy=item.get("animacy"),
                tags=item.get("tags"),
                paradigm=item.get("paradigm"),
            )

    def _load_text(self, path: Path) -> None:
        """Load vocabulary from text file."""
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                parts = line.split("|")
                if len(parts) < 2:
                    continue

                word = parts[0]
                pos = parts[1]
                gender = parts[2] if len(parts) > 2 else None
                animacy = parts[3] if len(parts) > 3 else None
                paradigm = parts[4] if len(parts) > 4 else None

                self.add(word, pos, gender, animacy, paradigm=paradigm)

    def save(self, file_path: str | Path) -> None:
        """Save vocabulary to JSON file.

        Args:
            file_path: Path to save vocabulary
        """
        path = Path(file_path)

        data = [
            {
                "word": w.word,
                "pos": w.pos,
                "gender": w.gender,
                "animacy": w.animacy,
                "tags": w.tags,
                "paradigm": w.paradigm,
            }
            for w in self._words.values()
        ]

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_domain(self, domain: str) -> None:
        """Load pre-made domain dictionary.

        Args:
            domain: Domain name (IT, medical, legal)

        Raises:
            ValueError: If domain is not available
        """
        # Pre-made domain dictionaries
        domains = {
            "IT": self._get_it_vocabulary(),
            "medical": self._get_medical_vocabulary(),
            "legal": self._get_legal_vocabulary(),
        }

        if domain not in domains:
            raise ValueError(f"Unknown domain: {domain}. Available: {list(domains.keys())}")

        for word in domains[domain]:
            self.add(**word)

    def _get_it_vocabulary(self) -> list[dict[str, Any]]:
        """Get IT domain vocabulary."""
        return [
            {"word": "блокчейн", "pos": "NOUN", "gender": "masc", "animacy": "inan"},
            {"word": "крипта", "pos": "NOUN", "gender": "fem", "animacy": "inan"},
            {"word": "майнинг", "pos": "NOUN", "gender": "masc", "animacy": "inan"},
            {"word": "фреймворк", "pos": "NOUN", "gender": "masc", "animacy": "inan"},
            {"word": "бэкенд", "pos": "NOUN", "gender": "masc", "animacy": "inan"},
            {"word": "фронтенд", "pos": "NOUN", "gender": "masc", "animacy": "inan"},
            {"word": "деплой", "pos": "NOUN", "gender": "masc", "animacy": "inan"},
            {"word": "коммит", "pos": "NOUN", "gender": "masc", "animacy": "inan"},
        ]

    def _get_medical_vocabulary(self) -> list[dict[str, Any]]:
        """Get medical domain vocabulary."""
        return [
            {"word": "диагноз", "pos": "NOUN", "gender": "masc", "animacy": "inan"},
            {"word": "терапия", "pos": "NOUN", "gender": "fem", "animacy": "inan"},
            {"word": "анамнез", "pos": "NOUN", "gender": "masc", "animacy": "inan"},
        ]

    def _get_legal_vocabulary(self) -> list[dict[str, Any]]:
        """Get legal domain vocabulary."""
        return [
            {"word": "истец", "pos": "NOUN", "gender": "masc", "animacy": "anim"},
            {"word": "ответчик", "pos": "NOUN", "gender": "masc", "animacy": "anim"},
            {"word": "иск", "pos": "NOUN", "gender": "masc", "animacy": "inan"},
        ]

    def __len__(self) -> int:
        """Get number of words in vocabulary."""
        return len(self._words)

    def __repr__(self) -> str:
        """String representation."""
        return f"<CustomVocabulary with {len(self)} words>"
