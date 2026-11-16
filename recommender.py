"""Explainable concept search and content-based recommendations.

Uses standard-library TF-IDF/cosine similarity plus a small phrase-match
boost. Book.content contains the catalog's deep index fields, so searches can
match concepts, subtopics, alternate terms, prerequisites and applications.
"""
import math
import re   #Regular expressions; searching and matching text patterns
from collections import Counter  # Counts how many times each word appears

STOPWORDS = {
    'a','an','the','of','in','on','for','to','and','or','is','are','was','were',
    'be','been','being','with','by','at','from','as','it','this','that','these',
    'those','i','you','we','they','he','she','his','her','their','its','about',
    'into','than','so','do','does','did','not','no','if','what','which','how',
    'explain','find','show','book','books','topic','topics',
}
TOKEN_RE = re.compile(r"[a-z0-9]+(?:[+#][a-z0-9]+)?", re.I) #re.I ignoring uppser/lower case


def tokenize(text):
    if not text:
        return []
    return [token for token in TOKEN_RE.findall(str(text).lower())
            if token not in STOPWORDS and len(token) > 1]


def _tf(tokens):
    counts = Counter(tokens)
    total = len(tokens)
    return {term: count / total for term, count in counts.items()} if total else {}


def _idf(token_lists):
    count = Counter(term for tokens in token_lists for term in set(tokens))
    n = len(token_lists)
    return {term: math.log((n + 1) / (freq + 1)) + 1 for term, freq in count.items()}


def _vector(tokens, idf):
    return {term: weight * idf.get(term, 0.0) for term, weight in _tf(tokens).items()}


def _cosine(a, b):
    if not a or not b:
        return 0.0
    common = a.keys() & b.keys()
    dot = sum(a[t] * b[t] for t in common)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0


def rank_by_similarity(query, documents, top_n=None, min_score=0.015):   #use in student.py
    """Return ``[(document_key, score), ...]`` in descending relevance order."""
    if not query or not documents:
        return []
    q = str(query).strip().lower()
    q_tokens = tokenize(q)
    if not q_tokens:
        return []
    keys = [key for key, _ in documents]
    texts = [str(text or '') for _, text in documents]
    token_lists = [tokenize(text) for text in texts]
    idf = _idf(token_lists + [q_tokens])
    qv = _vector(q_tokens, idf)
    q_phrases = {q}
    # Reward exact multi-word concepts and meaningful two-word phrases.
    q_phrases.update(' '.join(q_tokens[i:i+2]) for i in range(len(q_tokens)-1))
    results = []
    for key, text, tokens in zip(keys, texts, token_lists):
        score = _cosine(qv, _vector(tokens, idf))
        lowered = text.lower()
        if q in lowered:
            score += 0.30
        elif any(phrase in lowered for phrase in q_phrases if len(phrase) > 3):
            score += 0.10
        if score >= min_score:
            results.append((key, min(score, 1.0)))
    results.sort(key=lambda item: (-item[1], str(item[0])))
    return results[:top_n] if top_n else results
