"""Tests for CustomVocabulary."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from mawo import CustomVocabulary


class TestCustomVocabulary:
    """Test suite for CustomVocabulary."""

    def test_init(self) -> None:
        """Test vocabulary initialization."""
        vocab = CustomVocabulary()
        assert len(vocab) == 0

    def test_add_word(self) -> None:
        """Test adding a word."""
        vocab = CustomVocabulary()
        vocab.add("тест", pos="NOUN", gender="masc")

        assert vocab.has("тест")
        assert len(vocab) == 1

        word = vocab.get("тест")
        assert word is not None
        assert word.word == "тест"
        assert word.pos == "NOUN"
        assert word.gender == "masc"

    def test_add_word_case_insensitive(self) -> None:
        """Test that vocabulary is case-insensitive."""
        vocab = CustomVocabulary()
        vocab.add("Тест", pos="NOUN")

        assert vocab.has("тест")
        assert vocab.has("ТЕСТ")
        assert vocab.has("Тест")

    def test_load_domain_it(self) -> None:
        """Test loading IT domain."""
        vocab = CustomVocabulary()
        vocab.load_domain("IT")

        assert len(vocab) > 0
        assert vocab.has("блокчейн")

    def test_load_domain_unknown(self) -> None:
        """Test loading unknown domain raises error."""
        vocab = CustomVocabulary()

        with pytest.raises(ValueError, match="Unknown domain"):
            vocab.load_domain("unknown")

    def test_save_load_json(self) -> None:
        """Test saving and loading JSON."""
        vocab1 = CustomVocabulary()
        vocab1.add("тест1", pos="NOUN", gender="masc")
        vocab1.add("тест2", pos="VERB")

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "vocab.json"

            # Save
            vocab1.save(file_path)
            assert file_path.exists()

            # Load into new vocabulary
            vocab2 = CustomVocabulary()
            vocab2.load(file_path)

            assert len(vocab2) == 2
            assert vocab2.has("тест1")
            assert vocab2.has("тест2")

    def test_save_load_text(self) -> None:
        """Test loading text format."""
        vocab = CustomVocabulary()

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "vocab.txt"

            # Create text file
            file_path.write_text("тест1|NOUN|masc|inan\nтест2|VERB\n", encoding="utf-8")

            # Load
            vocab.load(file_path)

            assert len(vocab) == 2
            assert vocab.has("тест1")
            assert vocab.has("тест2")

    def test_repr(self) -> None:
        """Test string representation."""
        vocab = CustomVocabulary()
        vocab.add("тест", pos="NOUN")

        repr_str = repr(vocab)
        assert "CustomVocabulary" in repr_str
        assert "1 words" in repr_str
