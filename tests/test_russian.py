"""Tests for Russian class."""

from __future__ import annotations

from mawo import Russian


class TestRussian:
    """Test suite for Russian class."""

    def test_init(self) -> None:
        """Test Russian initialization."""
        nlp = Russian()
        assert nlp is not None
        assert nlp.vocab is not None

    def test_init_with_options(self) -> None:
        """Test initialization with options."""
        nlp = Russian(use_ner=False, use_syntax=False)
        assert nlp.use_ner is False
        assert nlp.use_syntax is False

    def test_call_simple_text(self) -> None:
        """Test processing simple text."""
        nlp = Russian(use_ner=False, use_syntax=False)
        doc = nlp("Привет мир")

        assert doc is not None
        assert doc.text == "Привет мир"
        assert len(doc.tokens) >= 2  # At least 2 tokens

    def test_custom_vocab_integration(self) -> None:
        """Test custom vocabulary integration."""
        nlp = Russian(use_ner=False, use_syntax=False)

        # Add custom word
        nlp.vocab.add("тестворд", pos="NOUN", gender="masc")

        # Process text with custom word
        doc = nlp("тестворд")

        # Check if custom word was used
        if doc.tokens:
            token = doc.tokens[0]
            assert token.text == "тестворд"

    def test_repr(self) -> None:
        """Test string representation."""
        nlp = Russian()
        repr_str = repr(nlp)
        assert "Russian" in repr_str
