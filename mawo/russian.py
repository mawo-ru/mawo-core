"""Russian language class - unified API for all MAWO libraries."""

from __future__ import annotations

import logging
from typing import Any

from .document import Document, Sentence, Token
from .vocab import CustomVocabulary

logger = logging.getLogger(__name__)


# Russian prepositions dictionary
# These should always be tagged as PREP, not NOUN/INTJ/etc.
RUSSIAN_PREPOSITIONS = {
    # Simple prepositions
    "в",
    "во",
    "на",
    "с",
    "со",
    "к",
    "ко",
    "по",
    "за",
    "из",
    "изо",
    "о",
    "об",
    "обо",
    "от",
    "ото",
    "до",
    "для",
    "при",
    "про",
    "без",
    "безо",
    "под",
    "подо",
    "над",
    "надо",
    "перед",
    "передо",
    "у",
    "через",
    "сквозь",
    "меж",
    "между",
    "вопреки",
    "согласно",
    # Compound prepositions (common ones)
    "из-за",
    "из-под",
    "по-над",
    "по-за",
}


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
        """Analyze morphology using pymorphy3 with context-aware disambiguation.

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

        # First pass: get all parses
        all_parses: list[list[Any]] = []
        for token in doc.tokens:
            # Check custom vocabulary first
            custom_word = self.vocab.get(token.text)
            if custom_word:
                token.lemma = custom_word.word.lower()
                token.pos = custom_word.pos
                token.tag = custom_word.pos
                all_parses.append([])  # Empty list for custom words
                continue

            # Get PyMorphy3 parses
            parses = self._morphology.parse(token.text)
            all_parses.append(parses)

            # Check prepositions (force PREP to fix PyMorphy3 misclassification)
            word_lower = token.text.lower()
            if word_lower in RUSSIAN_PREPOSITIONS:
                # Override POS to PREP but keep the parse for grammar checking
                token.lemma = word_lower
                token.pos = "PREP"
                token.tag = "PREP"
                # Keep first parse
                if parses:
                    token._morphology = parses[0]
                continue

            if not parses:
                continue

            # Store first parse temporarily
            parse = parses[0]
            token.lemma = getattr(parse, "normal_form", token.text)
            token.pos = getattr(parse.tag, "POS", None) if hasattr(parse, "tag") else None
            token.tag = str(parse.tag) if hasattr(parse, "tag") else None
            token._morphology = parse

        # Second pass: context-aware disambiguation
        self._disambiguate_with_context(doc, all_parses)

    def _disambiguate_with_context(self, doc: Document, all_parses: list[list[Any]]) -> None:
        """Disambiguate morphology using context (adjective-noun agreement).

        Args:
            doc: Document with tokens
            all_parses: All possible parses for each token
        """
        tokens = doc.tokens

        for i in range(len(tokens) - 1):
            current = tokens[i]
            next_token = tokens[i + 1]

            # Skip if no alternatives or already custom/preposition
            if not all_parses[i] or not all_parses[i + 1]:
                continue

            # Adjective-Noun agreement: match gender, case, number
            if current.pos == "ADJF" and next_token.pos in ("NOUN", "NPRO"):
                # Try to find a better parse for adjective that matches noun
                best_parse = self._find_matching_adjective_parse(all_parses[i], next_token)
                if best_parse:
                    current.lemma = getattr(best_parse, "normal_form", current.text)
                    if hasattr(best_parse, "tag"):
                        current.pos = getattr(best_parse.tag, "POS", None)
                    else:
                        current.pos = None
                    if hasattr(best_parse, "tag"):
                        current.tag = str(best_parse.tag)
                    else:
                        current.tag = None
                    current._morphology = best_parse

                # ALSO try to find better parse for NOUN that matches adjective
                # This fixes cases like "невидимой инвалидности" where:
                # - "невидимой" is correctly identified as gent/sing
                # - "инвалидности" defaults to nomn/plur but should be gent/sing
                best_noun_parse = self._find_matching_noun_parse(all_parses[i + 1], current)
                if best_noun_parse:
                    next_token.lemma = getattr(best_noun_parse, "normal_form", next_token.text)
                    if hasattr(best_noun_parse, "tag"):
                        next_token.pos = getattr(best_noun_parse.tag, "POS", None)
                    else:
                        next_token.pos = None
                    if hasattr(best_noun_parse, "tag"):
                        next_token.tag = str(best_noun_parse.tag)
                    else:
                        next_token.tag = None
                    next_token._morphology = best_noun_parse

            # Preposition-Noun case government
            elif current.pos == "PREP" and next_token.pos in ("NOUN", "NPRO", "ADJF"):
                # Try to find correct case for noun based on preposition
                best_parse = self._find_preposition_governed_case(
                    current.text.lower(), all_parses[i + 1], next_token
                )
                if best_parse:
                    next_token.lemma = getattr(best_parse, "normal_form", next_token.text)
                    if hasattr(best_parse, "tag"):
                        next_token.pos = getattr(best_parse.tag, "POS", None)
                    else:
                        next_token.pos = None
                    if hasattr(best_parse, "tag"):
                        next_token.tag = str(best_parse.tag)
                    else:
                        next_token.tag = None
                    next_token._morphology = best_parse

    def _find_matching_adjective_parse(self, parses: list[Any], noun: Token) -> Any:
        """Find adjective parse that matches noun gender/case/number.

        Args:
            parses: All possible parses for adjective
            noun: Noun token to match against

        Returns:
            Best matching parse or None
        """
        noun_gender = noun.gender
        noun_case = noun.case
        noun_number = noun.number

        # Try exact match first
        for parse in parses:
            if not hasattr(parse, "tag"):
                continue

            tag = parse.tag
            if (
                getattr(tag, "gender", None) == noun_gender
                and getattr(tag, "case", None) == noun_case
                and getattr(tag, "number", None) == noun_number
            ):
                return parse

        # No better match found
        return None

    def _find_matching_noun_parse(self, parses: list[Any], adjective: Token) -> Any:
        """Find noun parse that matches adjective gender/case/number.

        Args:
            parses: All possible parses for noun
            adjective: Adjective token to match against

        Returns:
            Best matching parse or None
        """
        if not hasattr(adjective, "_morphology") or not adjective._morphology:
            return None

        adj_tag = adjective._morphology.tag
        adj_gender = getattr(adj_tag, "gender", None)
        adj_case = getattr(adj_tag, "case", None)
        adj_number = getattr(adj_tag, "number", None)

        # Try exact match first
        for parse in parses:
            if not hasattr(parse, "tag"):
                continue

            tag = parse.tag

            # Check if this is a noun/pronoun
            if not hasattr(tag, "POS") or tag.POS not in ("NOUN", "NPRO"):
                continue

            # Match gender, case, and number with adjective
            noun_gender = getattr(tag, "gender", None)
            noun_case = getattr(tag, "case", None)
            noun_number = getattr(tag, "number", None)

            # Gender matching (only in singular)
            gender_match = True
            if adj_number == "sing" and noun_number == "sing":
                if adj_gender and noun_gender:
                    gender_match = adj_gender == noun_gender

            # Case and number must match
            case_match = (adj_case == noun_case) if (adj_case and noun_case) else True
            number_match = (adj_number == noun_number) if (adj_number and noun_number) else True

            if gender_match and case_match and number_match:
                return parse

        # If no exact match, try to match at least case and number
        for parse in parses:
            if not hasattr(parse, "tag"):
                continue

            tag = parse.tag
            if not hasattr(tag, "POS") or tag.POS not in ("NOUN", "NPRO"):
                continue

            noun_case = getattr(tag, "case", None)
            noun_number = getattr(tag, "number", None)

            # At least case and number should match
            if noun_case == adj_case and noun_number == adj_number:
                return parse

        # No better match found
        return None

    def _find_preposition_governed_case(
        self, preposition: str, parses: list[Any], noun: Token
    ) -> Any:
        """Find noun parse with correct case for preposition.

        Args:
            preposition: Preposition text (lowercase)
            parses: All possible parses for noun
            noun: Noun token

        Returns:
            Best matching parse or None
        """
        # Common preposition + case rules
        # в, на, о, об, при → prepositional (loct)
        # к, по → dative (datv)
        # с, от, из, до, для, без, у, около → genitive (gent)
        # через, про, за, на (direction) → accusative (accs)

        expected_case = None
        if preposition in ("в", "во", "на", "о", "об", "обо", "при"):
            # Can be both loct and accs depending on context
            # For static location: loct (в школе - in school)
            # For direction: accs (в школу - to school)
            # Default to loct for now
            expected_case = "loct"
        elif preposition in ("к", "ко", "по"):
            expected_case = "datv"
        elif preposition in (
            "с",
            "со",
            "от",
            "ото",
            "из",
            "изо",
            "до",
            "для",
            "без",
            "безо",
            "у",
            "около",
        ):
            expected_case = "gent"
        elif preposition in ("через", "про"):
            expected_case = "accs"

        if not expected_case:
            return None

        # Find parse with expected case
        for parse in parses:
            if not hasattr(parse, "tag"):
                continue

            tag = parse.tag
            if getattr(tag, "case", None) == expected_case:
                return parse

        return None

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
