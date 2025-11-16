# mawo-core

Unified API for Russian NLP - combines razdel, pymorphy3, slovnet, natasha into a single, spaCy-like interface.

## Features

- **Unified API** - Single entry point for all MAWO libraries
- **Rich Objects** - Document/Token/Span with lazy evaluation
- **Custom Vocabulary** - Runtime word additions without DAWG rebuilding
- **Modular Pipeline** - Compose only the components you need
- **spaCy-compatible** - Familiar API for spaCy users

## Installation

```bash
# Core (tokenization + morphology)
pip install mawo-core

# Full (with NER and syntax)
pip install mawo-core[all]
```

## Quick Start

```python
from mawo import Russian

# Create analyzer
nlp = Russian()

# Analyze text
doc = nlp("Александр Пушкин родился в Москве")

# Access tokens
for token in doc.tokens:
    print(token.text, token.lemma, token.pos, token.tag)

# Access entities (requires mawo-slovnet)
for ent in doc.entities:
    print(ent.text, ent.label)

# Access sentences
for sent in doc.sentences:
    print(sent.text)
```

## Advanced Usage

### Rich Token Objects

```python
doc = nlp("Я читал интересную книгу")

for token in doc.tokens:
    # Morphology (from pymorphy3)
    print(token.lemma)          # "читать"
    print(token.pos)            # "VERB"
    print(token.aspect)         # "imperfective"
    print(token.tense)          # "past"
    print(token.gender)         # "masc"

    # Syntax (from slovnet)
    print(token.dep)            # "ROOT"
    print(token.head)           # None

    # Context
    print(token.children)       # [книгу]
    print(token.ancestors)      # []
```

### Adjective-Noun Pairs

```python
doc = nlp("красивая дом")  # Error: gender mismatch

for pair in doc.adjective_noun_pairs:
    print(pair.adjective)       # Token("красивая")
    print(pair.noun)            # Token("дом")
    print(pair.agreement)       # "incorrect"
    print(pair.gender_match)    # False
    print(pair.suggestion)      # "красивый дом"
```

### Verb Aspects

```python
doc = nlp("Я прочитал книгу")

for verb in doc.verbs:
    print(verb.word)            # "прочитал"
    print(verb.aspect)          # "perfective"
    print(verb.is_perfective)   # True
    print(verb.aspect_pair)     # "читать"
```

### Custom Vocabulary

```python
from mawo import Russian

nlp = Russian()

# Add single word
nlp.vocab.add("блокчейн",
    pos="NOUN",
    gender="masc",
    animacy="inan",
    tags={"domain": "IT"}
)

# Load domain dictionary
nlp.vocab.load_domain("IT")  # блокчейн, API, фреймворк...

# Load from file
nlp.vocab.load("tech_terms.txt")

# Now custom words work
doc = nlp("Блокчейн это технология")
print(doc.tokens[0].pos)  # "NOUN" (from custom vocab)
```

### Custom Pipeline

```python
from mawo import Pipeline

# Minimal pipeline (fast)
nlp = Pipeline([
    "tokenizer",      # razdel
    "morphologizer",  # pymorphy3
])

# Full pipeline
nlp = Pipeline([
    "tokenizer",
    "morphologizer",
    "ner",           # slovnet
    "parser",        # slovnet syntax
])

# Custom pipeline
nlp = Pipeline([
    "tokenizer",
    ("custom", MyCustomComponent()),
    "morphologizer",
])
```

### Entity Preservation

```python
from mawo import Russian

nlp = Russian()

# Check entity preservation in translation
source = nlp("Alexander Pushkin was born in Moscow")
target = nlp("Александр Пушкин родился в Москве")

matches = nlp.match_entities(source, target)

for match in matches:
    print(match.source)         # Entity("Alexander Pushkin", "PER")
    print(match.target)         # Entity("Александр Пушкин", "PER")
    print(match.status)         # "matched"
    print(match.confidence)     # 0.95
```

## Performance

- **Tokenization**: ~5000 tokens/sec
- **Morphology**: ~5000 words/sec
- **NER**: ~1000 tokens/sec
- **Memory**: ~60MB (with slovnet)

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Code quality
black .
ruff check .
mypy mawo
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Part of MAWO Ecosystem

- [mawo-pymorphy3](https://github.com/mawo-ru/mawo-pymorphy3) - Morphological analysis
- [mawo-razdel](https://github.com/mawo-ru/mawo-razdel) - Tokenization
- [mawo-slovnet](https://github.com/mawo-ru/mawo-slovnet) - NER and syntax
- [mawo-natasha](https://github.com/mawo-ru/mawo-natasha) - Embeddings
- [mawo-grammar](https://github.com/mawo-ru/mawo-grammar) - Grammar checking
