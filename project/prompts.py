from langchain_core.prompts import ChatPromptTemplate

PROMPT_TEMPLATE = """
You are a MahaRERA Compliance Officer.

Agreement Clause:
{clause}

Legal Context:
{context}

Instructions:
- Use ONLY the provided legal context.
- The "status" field in the output JSON MUST be exactly one of: "Compliant", "Non-Compliant", or "Needs Review".
  - Use "Compliant" if the clause is fully aligned with MahaRERA rules/laws.
  - Use "Non-Compliant" if the clause violates or contradicts MahaRERA rules/laws.
  - Use "Needs Review" if the context is insufficient, unrelated, or if you cannot determine compliance.
- Return ONLY valid JSON.

Output schema:
{{
  "status": "Compliant / Non-Compliant / Needs Review",
  "confidence": 0,
  "reason": "Detailed legal reasoning for the status decision",
  "citations": [
    {{
      "document": "Exact name of the source document",
      "page": "Page number as string or number",
      "section": "Section or category name (e.g. acts, rules, regulations)"
    }}
  ],
  "recommendation": "Suggested action or revision to make it compliant, if non-compliant or needs review"
}}
"""

PROMPT_TEMPLATE = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)


BATCH_PROMPT_TEMPLATE = """
You are a MahaRERA Compliance Officer.
Analyze the following list of Agreement Clauses against their specific retrieved Legal Context.

For each clause:
1. Auditing instructions:
   - Use ONLY the provided legal context for that clause.
   - The "status" field in the output JSON MUST be exactly one of: "Compliant", "Non-Compliant", or "Needs Review".
     - Use "Compliant" if the clause is fully aligned with MahaRERA rules/laws.
     - Use "Non-Compliant" if the clause violates or contradicts MahaRERA rules/laws.
     - Use "Needs Review" if the context is insufficient, unrelated, or if you cannot determine compliance.
2. Return a valid JSON list containing an audit object for each input clause.

Output schema (JSON List of objects):
[
  {{
    "index": 1,
    "status": "Compliant / Non-Compliant / Needs Review",
    "confidence": 0,
    "reason": "Detailed legal reasoning for the status decision",
    "citations": [
      {{
        "document": "Exact name of the source document",
        "page": "Page number as string or number",
        "section": "Section or category name (e.g. acts, rules, regulations)"
      }}
    ],
    "recommendation": "Suggested action or revision to make it compliant, if non-compliant or needs review"
  }},
  ...
]

Input Clauses and Legal Context:
{clauses_with_context}
"""

BATCH_PROMPT_TEMPLATE = ChatPromptTemplate.from_template(BATCH_PROMPT_TEMPLATE)


