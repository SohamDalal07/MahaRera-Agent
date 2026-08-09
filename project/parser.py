import json
import re



def _normalize_parsed(data: dict) -> dict:
    if not isinstance(data, dict):
        return {
            "status": "Needs Review",
            "confidence": 0,
            "reason": "Parsed output is not a dictionary.",
            "citations": [],
            "recommendation": "",
        }

    # 1. Normalize status to exactly one of "Compliant", "Non-Compliant", or "Needs Review"
    status = str(data.get("status", "Needs Review")).strip()
    status_lower = status.lower()
    if "non-compliant" in status_lower or "non compliant" in status_lower or "violat" in status_lower:
        status_val = "Non-Compliant"
    elif "compliant" in status_lower or "success" in status_lower or "yes" in status_lower:
        status_val = "Compliant"
    else:
        status_val = "Needs Review"

    # 2. Normalize confidence score (e.g. scale float [0, 1.0] -> [0, 100])
    confidence_val = 0
    raw_conf = data.get("confidence", 0)
    try:
        val = float(raw_conf)
        if 0.0 < val <= 1.0:
            confidence_val = int(val * 100)
        else:
            confidence_val = int(val)
    except (ValueError, TypeError):
        pass

    confidence_val = max(0, min(100, confidence_val))

    # 3. Sanitize citations and recommendations
    citations_val = data.get("citations", [])
    if not isinstance(citations_val, list):
        citations_val = []

    reason_val = str(data.get("reason", ""))
    recommendation_val = str(data.get("recommendation", ""))

    return {
        "status": status_val,
        "confidence": confidence_val,
        "reason": reason_val,
        "citations": citations_val,
        "recommendation": recommendation_val,
    }


def parse_response(response_text) -> dict:
    if not response_text:
        return {
            "status": "Needs Review",
            "confidence": 0,
            "reason": "Empty response from model.",
            "citations": [],
            "recommendation": "",
        }

    # Normalize response_text if it is returned as a list of blocks or other structures
    if isinstance(response_text, list):
        parts = []
        for item in response_text:
            if isinstance(item, dict) and "text" in item:
                parts.append(item["text"])
            elif isinstance(item, str):
                parts.append(item)
        response_text = "".join(parts)
    elif isinstance(response_text, dict) and "text" in response_text:
        response_text = response_text["text"]
    elif not isinstance(response_text, str):
        response_text = str(response_text)

    cleaned = response_text.strip()

    # 1. Try loading directly first
    try:
        return _normalize_parsed(json.loads(cleaned))
    except json.JSONDecodeError:
        pass

    # 2. Try removing markdown code block delimiters (```json or ```)
    if cleaned.startswith("```"):
        # Remove starting ```json or ```
        cleaned_no_block = re.sub(r"^```(?:json)?\s*", "", cleaned)
        # Remove ending ```
        cleaned_no_block = re.sub(r"\s*```$", "", cleaned_no_block)
        try:
            return _normalize_parsed(json.loads(cleaned_no_block.strip()))
        except json.JSONDecodeError:
            pass

    # 3. Use regex to extract everything between the first '{' and the last '}'
    match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
    if match:
        extracted = match.group(1).strip()
        try:
            return _normalize_parsed(json.loads(extracted))
        except json.JSONDecodeError:
            pass

    # 4. Return fallback if all parsing attempts fail
    return {
        "status": "Needs Review",
        "confidence": 0,
        "reason": "Unable to parse model output as JSON.",
        "citations": [],
        "recommendation": "",
    }


def parse_batch_response(response_text) -> list[dict]:
    if not response_text:
        return []

    # Normalize response_text
    if isinstance(response_text, list):
        parts = []
        for item in response_text:
            if isinstance(item, dict) and "text" in item:
                parts.append(item["text"])
            elif isinstance(item, str):
                parts.append(item)
        response_text = "".join(parts)
    elif isinstance(response_text, dict) and "text" in response_text:
        response_text = response_text["text"]
    elif not isinstance(response_text, str):
        response_text = str(response_text)

    cleaned = response_text.strip()

    # Remove markdown code blocks if present
    if "```json" in cleaned:
        cleaned = cleaned.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```", 1)[1].split("```", 1)[0].strip()

    try:
        data = json.loads(cleaned)
        if isinstance(data, list):
            return [_normalize_parsed(x) for x in data]
        elif isinstance(data, dict):
            return [_normalize_parsed(data)]
    except json.JSONDecodeError:
        pass

    # Fallback to regex matching a JSON array
    match = re.search(r"(\[.*\])", cleaned, re.DOTALL)
    if match:
        extracted = match.group(1).strip()
        try:
            data = json.loads(extracted)
            if isinstance(data, list):
                return [_normalize_parsed(x) for x in data]
        except json.JSONDecodeError:
            pass

    return []



