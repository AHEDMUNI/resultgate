"""Deterministic citation integrity checks; never evaluates semantic support."""

from .extraction import bounded

MAX_SOURCES = 100
MAX_CITATIONS = 1000
MAX_TEXT_CHARS = 1_000_000
MAX_QUOTE_CHARS = 10_000
MAX_ID_CHARS = 256


def _identifier(value, label):
    if not isinstance(value, str) or not value.strip() or len(value) > MAX_ID_CHARS:
        raise ValueError(f"{label} must be a nonempty string of at most {MAX_ID_CHARS} characters")
    return value


def audit_citations(payload: dict) -> dict:
    """Check literal quotes and source identity in caller-supplied evidence.

    A pass means only that all supplied citations match supplied source text.
    Source authenticity, factual truth, entailment and uncited claims are not
    assessed. Text is compared exactly, without whitespace or Unicode changes.
    Offsets, when supplied, are Python Unicode character indices, end-exclusive.
    """
    bounded(payload)
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    if set(payload) - {"sources", "citations", "required_source_ids"}:
        raise ValueError("unknown payload field")
    sources = payload.get("sources")
    citations = payload.get("citations")
    required = payload.get("required_source_ids", [])
    if not isinstance(sources, list) or len(sources) > MAX_SOURCES:
        raise ValueError(f"sources must be a list of at most {MAX_SOURCES} items")
    if not isinstance(citations, list) or len(citations) > MAX_CITATIONS:
        raise ValueError(f"citations must be a list of at most {MAX_CITATIONS} items")
    if not isinstance(required, list) or len(required) > MAX_SOURCES:
        raise ValueError(f"required_source_ids must be a list of at most {MAX_SOURCES} items")
    source_map = {}
    total_chars = 0
    for source in sources:
        if not isinstance(source, dict) or set(source) != {"id", "text"}:
            raise ValueError("each source must contain exactly id and text")
        source_id = _identifier(source["id"], "source.id")
        if source_id in source_map:
            raise ValueError("duplicate source id")
        if not isinstance(source["text"], str):
            raise ValueError("source.text must be a string")
        total_chars += len(source["text"])
        if total_chars > MAX_TEXT_CHARS:
            raise ValueError(f"combined source text exceeds {MAX_TEXT_CHARS} characters")
        source_map[source_id] = source["text"]
    required_ids = [_identifier(item, "required source id") for item in required]
    if len(set(required_ids)) != len(required_ids):
        raise ValueError("duplicate required source id")
    for citation in citations:
        if not isinstance(citation, dict):
            raise ValueError("each citation must be an object")
        if set(citation) - {"source_id", "quote", "start", "end"}:
            raise ValueError("unknown citation field")
        _identifier(citation.get("source_id"), "citation.source_id")
        quote = citation.get("quote")
        if not isinstance(quote, str) or not quote.strip() or len(quote) > MAX_QUOTE_CHARS:
            raise ValueError(f"quote must be nonempty and at most {MAX_QUOTE_CHARS} characters")
        if ("start" in citation) != ("end" in citation):
            raise ValueError("start and end must be supplied together")
        if "start" in citation:
            start, end = citation["start"], citation["end"]
            if type(start) is not int or type(end) is not int or not 0 <= start < end:
                raise ValueError("offsets must be integers satisfying 0 <= start < end")

    search_budget = sum(len(source_map.get(c["source_id"], "")) for c in citations if "start" not in c)
    if search_budget > 20_000_000:
        raise ValueError("citation search budget exceeded; split the batch or provide offsets")

    findings = []
    cited_ids = set()
    for index, citation in enumerate(citations):
        source_id, quote = citation["source_id"], citation["quote"]
        cited_ids.add(source_id)
        context = {"citation_index": index, "source_id": source_id}
        if source_id not in source_map:
            findings.append({"code": "SOURCE_NOT_FOUND", **context})
            continue
        text = source_map[source_id]
        if "start" in citation:
            start, end = citation["start"], citation["end"]
            if end > len(text):
                findings.append({"code": "OFFSET_OUT_OF_RANGE", **context})
            elif text[start:end] != quote:
                findings.append({"code": "QUOTE_OFFSET_MISMATCH", **context})
        elif quote not in text:
            findings.append({"code": "QUOTE_NOT_FOUND", **context})
    for source_id in required_ids:
        if source_id not in source_map:
            findings.append({"code": "REQUIRED_SOURCE_NOT_FOUND", "source_id": source_id})
        if source_id not in cited_ids:
            findings.append({"code": "REQUIRED_SOURCE_NOT_CITED", "source_id": source_id})
    if not citations:
        findings.append({"code": "NO_CITATIONS"})
    # No citations is explicitly unknown even if required evidence is absent.
    status = "unknown" if not citations else ("fail" if findings else "pass")
    return {
        "status": status,
        "semantic_support": "not_evaluated",
        "findings": findings,
        "citations_checked": len(citations),
        "sources_supplied": len(sources),
        "comparison": "exact_literal_unicode_codepoints",
    }
