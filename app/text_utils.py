from __future__ import annotations

import re
from collections import Counter
from pathlib import Path


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "do",
    "does",
    "for",
    "from",
    "how",
    "i",
    "if",
    "in",
    "is",
    "it",
    "my",
    "of",
    "on",
    "or",
    "the",
    "to",
    "what",
    "when",
    "where",
    "who",
    "with",
    "you",
    "your",
}


CATEGORY_KEYWORDS: dict[str, set[str]] = {
    "hr": {"employee", "onboarding", "leave", "benefit", "attendance", "performance", "salary"},
    "finance": {"reimbursement", "expense", "invoice", "payment", "budget", "travel", "procurement", "approval"},
    "it": {"account", "vpn", "device", "permission", "access", "ticket", "software", "github"},
    "engineering": {"deploy", "deployment", "api", "code", "review", "database", "incident", "rollback", "repository"},
    "security": {"security", "credential", "password", "access", "permission", "audit", "compliance"},
    "legal": {"contract", "legal", "privacy", "terms", "compliance", "policy"},
}


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "document"


def tokenize(text: str) -> list[str]:
    terms = re.findall(r"[\w\u4e00-\u9fff]+", text.lower())
    return [term for term in terms if len(term) > 1 and term not in STOPWORDS]


def top_terms(text: str, limit: int = 12) -> list[str]:
    counts = Counter(tokenize(text))
    return [term for term, _ in counts.most_common(limit)]


def title_from_markdown(path: Path, text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip() or path.stem.replace("_", " ").title()
    return path.stem.replace("_", " ").title()


def summarize_markdown(text: str, max_chars: int = 240) -> str:
    lines = []
    in_front_matter = False
    for idx, raw in enumerate(text.splitlines()):
        line = raw.strip()
        if idx == 0 and line == "---":
            in_front_matter = True
            continue
        if in_front_matter:
            if line == "---":
                in_front_matter = False
            continue
        if line and not line.startswith("#") and not line.startswith("|"):
            lines.append(re.sub(r"\s+", " ", line))
        if sum(len(line) for line in lines) > max_chars:
            break
    summary = " ".join(lines).strip()
    return summary[:max_chars].rstrip()


def score_text(query_terms: set[str], candidate_text: str) -> float:
    if not query_terms:
        return 0.0
    candidate_terms = set(tokenize(candidate_text))
    overlap = query_terms & candidate_terms
    return len(overlap) / len(query_terms)


def infer_categories(text: str, minimum: int = 1) -> list[str]:
    terms = set(tokenize(text))
    scores = []
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = len(terms & keywords)
        if score:
            scores.append((score, category))
    scores.sort(reverse=True)
    categories = [category for _, category in scores]
    return categories or ["general"][:minimum]

