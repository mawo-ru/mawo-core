"""Russian language class - unified API for all MAWO libraries."""

from __future__ import annotations

import logging
from typing import Any

from .document import Document, Sentence, Token
from .vocab import CustomVocabulary

logger = logging.getLogger(__name__)


class Russian:
    """Unified API for Russian NLP processing.

    Combines razdel, pymorphy3, slovnet, and natasha into a single interface.

    Example:
        >>> nlp = Russian()
        >>> doc = nlp("Александр Пушкин родился в Москве")
        >>> for token in doc.tokens:
        ...     print(token.text, token.lemma, token.pos)
    """

    def __init__(
        self,
        use_ner: bool = True,
        use_syntax: bool = True,
        use_embeddings: bool = False,
    ) -> None:
        """Initialize Russian NLP processor.

        Args:
            use_ner: Enable NER (requires mawo-slovnet)
            use_syntax: Enable syntax parsing (requires mawo-slovnet)
            use_embeddings: Enable embeddings (requires mawo-natasha)
        """
        self.use_ner = use_ner
        self.use_syntax = use_syntax
        self.use_embeddings = use_embeddings

        # Custom vocabulary
        self.vocab = CustomVocabulary()

        # Initialize components (lazy)
        self._tokenizer: Any = None
        self._morphology: Any = None
        self._ner_tagger: Any = None
        self._syntax_parser: Any = None

    def __call__(self, text: str) -> Document:
        """Process text and return Document.

        Args:
            text: Text to process

        Returns:
            Document with tokens, entities, etc.

        Example:
            >>> doc = nlp("Привет мир")
            >>> len(doc.tokens)
            2
        """
        doc = Document(text)

        # 1. Tokenization (always)
        self._tokenize(doc)

        # 2. Morphology (always)
        self._analyze_morphology(doc)

        # 3. Sentence segmentation (always)
        self._segment_sentences(doc)

        # 4. NER (optional)
        if self.use_ner:
            self._tag_ner(doc)

        # 5. Syntax parsing (optional)
        if self.use_syntax:
            self._parse_syntax(doc)

        return doc

    def _tokenize(self, doc: Document) -> None:
        """Tokenize text using razdel.

        Args:
            doc: Document to tokenize
        """
        if self._tokenizer is None:
            try:
                from mawo_razdel import tokenize

                self._tokenizer = tokenize
            except ImportError:
                logger.error("mawo-razdel not installed. Install: pip install mawo-razdel")
                return

        # Tokenize
        razdel_tokens = list(self._tokenizer(doc.text))

        # Convert to our Token objects
        for rt in razdel_tokens:
            token = Token(
                text=rt.text,
                start=rt.start,
                end=rt.stop,
            )
            doc.tokens.append(token)

    def _analyze_morphology(self, doc: Document) -> None:
        """Analyze morphology using pymorphy3.

        Args:
            doc: Document with tokens
        """
        if self._morphology is None:
            try:
                from mawo_pymorphy3 import create_analyzer

                self._morphology = create_analyzer()
            except ImportError:
                logger.error("mawo-pymorphy3 not installed")
                return

        # Analyze each token
        for token in doc.tokens:
            # Check custom vocabulary first
            custom_word = self.vocab.get(token.text)
            if custom_word:
                token.lemma = custom_word.word.lower()
                token.pos = custom_word.pos
                token.tag = custom_word.pos  # Simplified
                continue

            # Use pymorphy3
            parses = self._morphology.parse(token.text)
            if not parses:
                continue

            parse = parses[0]  # Best parse

            # Extract morphology
            token.lemma = getattr(parse, "normal_form", token.text)
            token.pos = getattr(parse.tag, "POS", None) if hasattr(parse, "tag") else None
            token.tag = str(parse.tag) if hasattr(parse, "tag") else None

            # Store full parse for later use
            token._morphology = parse

    def _segment_sentences(self, doc: Document) -> None:
        """Segment text into sentences using razdel.

        Args:
            doc: Document with tokens
        """
        try:
            from mawo_razdel import sentenize

            sentences = list(sentenize(doc.text))

            for sent in sentences:
                # Find tokens in this sentence
                sent_tokens = [
                    t for t in doc.tokens if t.start >= sent.start and t.end <= sent.stop
                ]

                doc.sentences.append(
                    Sentence(
                        text=sent.text,
                        start=sent.start,
                        end=sent.stop,
                        tokens=sent_tokens,
                    )
                )
        except ImportError:
            logger.debug("Sentence segmentation skipped (razdel not available)")

    def _tag_ner(self, doc: Document) -> None:
        """Tag named entities using slovnet.

        Args:
            doc: Document with tokens
        """
        if self._ner_tagger is None:
            try:
                from mawo_slovnet import NewsNERTagger

                self._ner_tagger = NewsNERTagger()
            except ImportError:
                logger.debug("NER skipped (mawo-slovnet not installed)")
                return

        try:
            # Get token texts
            token_texts = [t.text for t in doc.tokens]

            # Tag NER
            markup = self._ner_tagger([token_texts])
            if not markup:
                return

            # Extract entities (simplified - real implementation needs BIO parsing)
            # For now, just create placeholder
            # Real implementation would parse BIO tags from slovnet
        except Exception as e:
            logger.warning(f"NER failed: {e}")

    def _parse_syntax(self, doc: Document) -> None:
        """Parse syntax using slovnet.

        Args:
            doc: Document with tokens
        """
        if self._syntax_parser is None:
            try:
                from mawo_slovnet import NewsSyntaxParser

                self._syntax_parser = NewsSyntaxParser()
            except ImportError:
                logger.debug("Syntax parsing skipped (mawo-slovnet not installed)")
                return

        try:
            # Get token texts
            token_texts = [t.text for t in doc.tokens]

            # Parse syntax
            markup = self._syntax_parser([token_texts])
            if not markup:
                return

            # Extract syntax (simplified)
            # Real implementation would extract head_id and dep from slovnet
        except Exception as e:
            logger.warning(f"Syntax parsing failed: {e}")

    def match_entities(
        self,
        source_doc: Document,
        target_doc: Document,
    ) -> list[dict[str, Any]]:
        """Match entities between source and target documents.

        Args:
            source_doc: Source language document
            target_doc: Target language document

        Returns:
            List of entity matches

        Example:
            >>> source = nlp("Alexander Pushkin")
            >>> target = nlp("Александр Пушкин")
            >>> matches = nlp.match_entities(source, target)
        """
        matches = []

        # Simple matching based on entity order
        # Real implementation would use more sophisticated matching

        for src_ent, tgt_ent in zip(source_doc.entities, target_doc.entities):
            matches.append(
                {
                    "source": src_ent,
                    "target": tgt_ent,
                    "status": "matched",  # or "missing", "extra"
                    "confidence": 0.95,
                }
            )

        return matches

    def check_entity_preservation(
        self,
        source_doc: Document,
        target_doc: Document,
    ) -> list[dict[str, Any]]:
        """Check entity preservation between documents.

        Args:
            source_doc: Source document
            target_doc: Target document

        Returns:
            List of preservation errors
        """
        errors = []

        # Check for missing entities
        if len(source_doc.entities) != len(target_doc.entities):
            errors.append(
                {
                    "type": "count_mismatch",
                    "source_count": len(source_doc.entities),
                    "target_count": len(target_doc.entities),
                }
            )

        return errors

    def __repr__(self) -> str:
        """String representation."""
        features = []
        if self.use_ner:
            features.append("NER")
        if self.use_syntax:
            features.append("syntax")
        if self.use_embeddings:
            features.append("embeddings")

        features_str = ", ".join(features) if features else "basic"
        return f"<Russian({features_str})>"
