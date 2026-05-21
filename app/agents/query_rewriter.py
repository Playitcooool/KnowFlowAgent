from __future__ import annotations

from app.text_utils import tokenize


SYNONYMS = {
    "approve": ["approval", "approver", "review"],
    "approval": ["approve", "approver", "review"],
    "reimbursement": ["expense", "claim", "invoice"],
    "expense": ["reimbursement", "cost", "invoice"],
    "access": ["permission", "account", "authorization"],
    "github": ["repository", "repo", "permission"],
    "new": ["onboarding", "employee", "starter"],
    "employee": ["staff", "onboarding", "hr"],
    "deploy": ["deployment", "release", "rollback"],
    "incident": ["outage", "response", "postmortem"],
}


class QueryRewriter:
    def rewrite(self, query: str, n: int = 5, retry_level: int = 1) -> list[str]:
        terms = tokenize(query)
        queries = [query]
        if terms:
            queries.append(" ".join(terms))
        expanded = []
        for term in terms:
            expanded.append(term)
            expanded.extend(SYNONYMS.get(term, []))
        if expanded:
            queries.append(" ".join(dict.fromkeys(expanded)))
        for term in terms:
            for synonym in SYNONYMS.get(term, []):
                queries.append(query.replace(term, synonym))
        if retry_level >= 2 and terms:
            queries.extend(terms)
        if retry_level >= 4:
            queries.append(" ".join(terms[: max(1, len(terms) // 2)]))
        return self._unique(queries)[:n]

    def _unique(self, values: list[str]) -> list[str]:
        seen = set()
        out = []
        for value in values:
            normalized = " ".join(value.split())
            if normalized and normalized.lower() not in seen:
                seen.add(normalized.lower())
                out.append(normalized)
        return out

