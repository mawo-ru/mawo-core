"""MAWO Core - Unified API for Russian NLP.

This package provides a spaCy-like unified interface for all MAWO libraries:
- mawo-razdel: Tokenization
- mawo-pymorphy3: Morphology
- mawo-slovnet: NER and syntax (optional)
- mawo-natasha: Embeddings (optional)

Example:
    >>> from mawo import Russian
    >>> nlp = Russian()
    >>> doc = nlp("Александр Пушкин родился в Москве")
    >>> for token in doc.tokens:
    ...     print(token.text, token.lemma, token.pos)
"""

from __future__ import annotations

from .document import Document, Entity, Span, Token
from .russian import Russian
from .vocab import CustomVocabulary

__version__ = "0.1.0"

__all__ = [
    "Russian",
    "Document",
    "Token",
    "Span",
    "Entity",
    "CustomVocabulary",
]
