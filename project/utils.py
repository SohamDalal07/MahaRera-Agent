import re


CLAUSE_PATTERN = re.compile(
    r'(?m)(^\d+(?:\.\d+)+\b.*?)(?=^\d+(?:\.\d+)+\b|\Z)',
    re.DOTALL,
)

EXCLUDE_HEADERS = [
    "annexure",
    "schedule",
    "price table",
    "payment schedule",
    "amenities",
    "specifications",
    "floor plan",
    "inventory",
]


def is_definition_clause(text: str) -> bool:
    return bool(re.search(
        r'\bshall\s+(?:mean|have the meaning|include|refer to|constitute)\b|\bmeans\b',
        text,
        flags=re.IGNORECASE,
    ))


def is_table_clause(text: str) -> bool:
    text = text.strip()
    if len(text) < 120 and re.search(r'\b\d+\s+BHK\b', text, flags=re.IGNORECASE):
        return True
    if len(text) < 100 and re.search(r'^\s*\d+\s+\S+', text, flags=re.MULTILINE):
        return True
    if re.search(r'(^|\n)(Annexure|Schedule|Appendix|Table|Sr\.\s*No\.|Particulars|Common Areas)',
                 text,
                 flags=re.IGNORECASE):
        return True
    for header in EXCLUDE_HEADERS:
        if header in text.lower():
            return True
    return False


def is_valid_clause(text: str) -> bool:
    if is_definition_clause(text):
        return True
    if is_table_clause(text):
        return False
    if len(text.split()) < 20:
        return False
    if re.search(
        r'\b(shall|must|may|liable|obliged|agreement|promoter|allottee|possession|maintenance|notice|payment|registration|completion|occupancy|development)\b',
        text,
        flags=re.IGNORECASE,
    ):
        return True
    return len(text) > 160


def extract_clauses(text: str) -> list[str]:
    matches = [m.group(1).strip() for m in CLAUSE_PATTERN.finditer(text)]
    return [m for m in matches if m and m.strip() and is_valid_clause(m)]
