"""Document, Token, Span and Entity classes for Russian NLP."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Token:
    """Represents a single token in a document.

    Attributes:
        text: Token text
        start: Character start position
        end: Character end position
        lemma: Lemma (normal form)
        pos: Part of speech (NOUN, VERB, etc.)
        tag: Full morphological tag
        dep: Dependency relation (nsubj, obj, etc.)
        head_id: ID of head token in dependency tree
        _morphology: Internal morphology data from pymorphy3
        _syntax: Internal syntax data from slovnet
    """

    text: str
    start: int
    end: int
    lemma: str | None = None
    pos: str | None = None
    tag: str | None = None
    dep: str | None = None
    head_id: int | None = None
    _morphology: Any = None
    _syntax: Any = None

    @property
    def aspect(self) -> str | None:
        """Verb aspect (perfective/imperfective)."""
        if self._morphology and hasattr(self._morphology, "tag"):
            return getattr(self._morphology.tag, "aspect", None)
        return None

    @property
    def tense(self) -> str | None:
        """Verb tense."""
        if self._morphology and hasattr(self._morphology, "tag"):
            return getattr(self._morphology.tag, "tense", None)
        return None

    @property
    def gender(self) -> str | None:
        """Gender (masculine/feminine/neuter)."""
        if self._morphology and hasattr(self._morphology, "tag"):
            return getattr(self._morphology.tag, "gender", None)
        return None

    @property
    def case(self) -> str | None:
        """Grammatical case."""
        if self._morphology and hasattr(self._morphology, "tag"):
            return getattr(self._morphology.tag, "case", None)
        return None

    @property
    def number(self) -> str | None:
        """Grammatical number (singular/plural)."""
        if self._morphology and hasattr(self._morphology, "tag"):
            return getattr(self._morphology.tag, "number", None)
        return None

    def __repr__(self) -> str:
        """String representation."""
        return f"Token('{self.text}', pos={self.pos})"


@dataclass
class Span:
    """Represents a span of tokens in a document.

    Attributes:
        start: Start token index
        end: End token index
        tokens: List of tokens in this span
        label: Optional label (for NER)
    """

    start: int
    end: int
    tokens: list[Token]
    label: str | None = None

    @property
    def text(self) -> str:
        """Get text of this span."""
        return " ".join(t.text for t in self.tokens)

    def __repr__(self) -> str:
        """String representation."""
        return f"Span('{self.text}', label={self.label})"


@dataclass
class Entity(Span):
    """Represents a named entity (PER, LOC, ORG, etc.)."""

    def __repr__(self) -> str:
        """String representation."""
        return f"Entity('{self.text}', {self.label})"


@dataclass
class Sentence:
    """Represents a sentence in a document.

    Attributes:
        text: Sentence text
        start: Start character position
        end: End character position
        tokens: Tokens in this sentence
    """

    text: str
    start: int
    end: int
    tokens: list[Token] = field(default_factory=list)

    def __repr__(self) -> str:
        """String representation."""
        return f"Sentence('{self.text[:50]}...')"


@dataclass
class AdjectiveNounPair:
    """Represents an adjective-noun pair for agreement checking.

    Attributes:
        adjective: Adjective token
        noun: Noun token
        agreement: Agreement status ('correct', 'incorrect', 'unknown')
    """

    adjective: Token
    noun: Token
    agreement: str = "unknown"

    @property
    def gender_match(self) -> bool:
        """Check if genders match."""
        if self.adjective.gender and self.noun.gender:
            return self.adjective.gender == self.noun.gender
        return True  # Unknown

    @property
    def case_match(self) -> bool:
        """Check if cases match."""
        if self.adjective.case and self.noun.case:
            return self.adjective.case == self.noun.case
        return True

    @property
    def number_match(self) -> bool:
        """Check if numbers match."""
        if self.adjective.number and self.noun.number:
            return self.adjective.number == self.noun.number
        return True

    def suggest_correction(self) -> str | None:
        """Suggest corrected form."""
        if self.agreement == "correct":
            return None

        # Try to inflect adjective to match noun
        if self.adjective._morphology and hasattr(self.adjective._morphology, "inflect"):
            required_tags = set()
            if self.noun.gender:
                required_tags.add(self.noun.gender)
            if self.noun.case:
                required_tags.add(self.noun.case)
            if self.noun.number:
                required_tags.add(self.noun.number)

            inflected = self.adjective._morphology.inflect(required_tags)
            if inflected and hasattr(inflected, "word"):
                return f"{inflected.word} {self.noun.text}"

        return None


class Document:
    """Represents a processed document with tokens, entities, etc.

    This is the main result object returned by Russian().

    Attributes:
        text: Original text
        tokens: List of tokens
        sentences: List of sentences
        entities: List of named entities
    """

    def __init__(self, text: str) -> None:
        """Initialize document.

        Args:
            text: Original text
        """
        self.text = text
        self.tokens: list[Token] = []
        self.sentences: list[Sentence] = []
        self.entities: list[Entity] = []
        self._adjective_noun_pairs: list[AdjectiveNounPair] | None = None

    @property
    def adjective_noun_pairs(self) -> list[AdjectiveNounPair]:
        """Get adjective-noun pairs (lazy evaluation).

        Returns:
            List of adjective-noun pairs found in document
        """
        if self._adjective_noun_pairs is None:
            self._adjective_noun_pairs = self._find_adjective_noun_pairs()
        return self._adjective_noun_pairs

    def _find_adjective_noun_pairs(self) -> list[AdjectiveNounPair]:
        """Find adjective-noun pairs in document."""
        pairs: list[AdjectiveNounPair] = []

        # Simple heuristic: adjacent ADJF + NOUN
        for i in range(len(self.tokens) - 1):
            adj = self.tokens[i]
            noun = self.tokens[i + 1]

            if adj.pos == "ADJF" and noun.pos in ("NOUN", "NPRO"):
                # Check agreement
                agreement = "correct"
                if not (
                    adj.gender == noun.gender
                    and adj.case == noun.case
                    and adj.number == noun.number
                ):
                    agreement = "incorrect"

                pairs.append(AdjectiveNounPair(adjective=adj, noun=noun, agreement=agreement))

        return pairs

    @property
    def verbs(self) -> list[Token]:
        """Get all verbs in document.

        Returns:
            List of verb tokens
        """
        return [t for t in self.tokens if t.pos in ("VERB", "INFN")]

    def __iter__(self) -> Iterator[Token]:
        """Iterate over tokens."""
        return iter(self.tokens)

    def __len__(self) -> int:
        """Get number of tokens."""
        return len(self.tokens)

    def __repr__(self) -> str:
        """String representation."""
        return f"Document('{self.text[:50]}...', {len(self.tokens)} tokens)"
