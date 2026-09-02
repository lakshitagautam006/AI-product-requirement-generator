import re
import json
from typing import Dict, Any


def sanitize_filename(name: str) -> str:
    """Generate a clean, safe filename from product name."""
    clean = re.sub(r'[^\w\s-]', '', name).strip().lower()
    clean = re.sub(r'[-\s]+', '_', clean)
    return clean or "product_prd"


def extract_sections(full_text: str) -> Dict[str, str]:
    """Split the full PRD markdown text into discrete numbered sections for easy tab display."""
    sections = {
        "Executive Summary": "",
        "Problem Statement": "",
        "Personas": "",
        "Scope & Boundaries": "",
        "User Stories": "",
        "Functional Requirements": "",
        "Non-Functional Requirements": "",
        "Risk Matrix": ""
    }

    if not full_text:
        return sections

    # Flexible, unicode-resilient heading patterns matching markdown headers with or without numbering (h1 to h4)
    patterns = {
        "Executive Summary": r"(?:^|\n)(#{1,4}\s*(?:1[\.\)]\s*)?Executive Summary.*?(?=(?:\n#{1,4}\s*(?:2[\.\)]\s*)?Problem|\Z)))",
        "Problem Statement": r"(?:^|\n)(#{1,4}\s*(?:2[\.\)]\s*)?Problem Statement.*?(?=(?:\n#{1,4}\s*(?:3[\.\)]\s*)?(?:User )?Personas|\Z)))",
        "Personas": r"(?:^|\n)(#{1,4}\s*(?:3[\.\)]\s*)?(?:User )?Personas.*?(?=(?:\n#{1,4}\s*(?:4[\.\)]\s*)?Scope|\Z)))",
        "Scope & Boundaries": r"(?:^|\n)(#{1,4}\s*(?:4[\.\)]\s*)?Scope.*?(?=(?:\n#{1,4}\s*(?:5[\.\)]\s*)?User Stories|\Z|(?:\n---\s*\n))))",
        "User Stories": r"(?:^|\n)(#{1,4}\s*(?:5[\.\)]\s*)?User Stories.*?(?=(?:\n#{1,4}\s*(?:6[\.\)]\s*)?Functional Requirements|\Z)))",
        "Functional Requirements": r"(?:^|\n)(#{1,4}\s*(?:6[\.\)]\s*)?Functional Requirements.*?(?=(?:\n#{1,4}\s*(?:7[\.\)]\s*)?Non[-‑_ ]?Functional|\Z)))",
        "Non-Functional Requirements": r"(?:^|\n)(#{1,4}\s*(?:7[\.\)]\s*)?Non[-‑_ ]?Functional.*?(?=(?:\n#{1,4}\s*(?:8[\.\)]\s*)?Risk|\Z)))",
        "Risk Matrix": r"(?:^|\n)(#{1,4}\s*(?:8[\.\)]\s*)?Risk.*?(?=\Z))"
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, full_text, re.DOTALL | re.IGNORECASE)
        if match:
            sections[key] = match.group(1).strip()

    return sections


def count_user_stories(full_text: str, us_section: str = "") -> int:
    """Count the actual individual user stories present in the document."""
    text = us_section if us_section and len(us_section.strip()) > 30 else ""
    if not text:
        match = re.search(r"(?:^|\n)(#{1,4}\s*(?:5[\.\)]\s*)?User Stories.*?(?=(?:\n#{1,4}\s*(?:6[\.\)]\s*)?Functional|\Z)))", full_text, re.DOTALL | re.IGNORECASE)
        text = match.group(1) if match else full_text

    # 1. Unique US-001 / US‑001 / US01 IDs in the User Story section
    us_ids = set(re.findall(r"\bUS[-‑_]?\d+\b", text, re.IGNORECASE))
    if len(us_ids) >= 1:
        return len(us_ids)

    # 2. Table rows in User Stories section (excluding header/delimiter)
    us_table_rows = [
        line for line in text.split("\n")
        if line.strip().startswith("|")
        and not re.search(r"\|\s*[-:]+[-| :]+\|", line)
        and not re.search(r"(?i)\|\s*(?:#|ID|User Story|Story)\s*\|", line)
    ]
    if len(us_table_rows) >= 1:
        return len(us_table_rows)

    # 3. Story header titles (### Story 1, **User Story 1:**, 1. **User Story 1**, etc.)
    header_patterns = [
        r"(?i)(?:^|\n)\s*#{2,5}\s*(?:User\s+)?Story\s*(?:\d+|[A-ZIVX]+)?[:\s\-\.]",
        r"(?i)(?:^|\n)\s*\d+\.\s+\*?\*?(?:User\s+)?Story\s*(?:\d+|[A-ZIVX]+)?[:\s\-\.]",
        r"(?i)\*\*(?:User\s+)?Story\s*\d+[:\s\-\.]",
        r"(?i)###\s+Story\s+\d+",
        r"(?i)###\s+User\s+Story\s+\d+",
    ]
    for pat in header_patterns:
        matches = re.findall(pat, text)
        if len(matches) >= 1:
            return len(matches)

    # 4. Agile "As a... I want..." statements
    as_a_matches = re.findall(r"(?i)\bAs\s+an?\s+(?:(?!\bAs\s+an?\b).){3,250}?\bI\s+(?:want|need|would\s+like|wish)\b", text, re.DOTALL)
    if len(as_a_matches) >= 1:
        return len(as_a_matches)

    # 5. Gherkin story acceptance blocks
    given_matches = re.findall(r"(?i)(?:^|\n)\s*[-*]?\s*\**Given\**\b", text)
    if len(given_matches) >= 1:
        return len(given_matches)

    return 0


def count_functional_requirements(full_text: str, fr_section: str = "") -> int:
    """Count the actual functional requirements present in the document."""
    text = fr_section if fr_section and len(fr_section.strip()) > 30 else ""
    if not text:
        match = re.search(r"(?:^|\n)(#{1,4}\s*(?:6[\.\)]\s*)?Functional Requirements.*?(?=(?:\n#{1,4}\s*(?:7[\.\)]\s*)?Non[-‑_ ]?Functional|\Z)))", full_text, re.DOTALL | re.IGNORECASE)
        text = match.group(1) if match else full_text

    # 1. Unique FR-001 / FR01 / REQ-001 IDs in the FR section
    fr_ids = set(re.findall(r"\b(?:FR|REQ)[-‑_]?\d+\b", text, re.IGNORECASE))
    if len(fr_ids) >= 1:
        return len(fr_ids)

    # 2. Table rows in Functional Requirements section
    fr_table_rows = [
        line for line in text.split("\n")
        if line.strip().startswith("|")
        and not re.search(r"\|\s*[-:]+[-| :]+\|", line)
        and not re.search(r"(?i)\|\s*(?:Req\s*ID|ID|Module|Requirement|Feature)\s*\|", line)
    ]
    if len(fr_table_rows) >= 1:
        return len(fr_table_rows)

    # 3. MoSCoW priorities count
    table_rows_p = len(re.findall(r"\|\s*P[0-2]\b", text, re.IGNORECASE))
    if table_rows_p >= 1:
        return table_rows_p

    return 0


def count_risks(full_text: str, risk_section: str = "") -> int:
    """Count the actual risk items present in the document."""
    text = risk_section if risk_section and len(risk_section.strip()) > 30 else ""
    if not text:
        match = re.search(r"(?:^|\n)(#{1,4}\s*(?:8[\.\)]\s*)?Risk.*?(?=\Z))", full_text, re.DOTALL | re.IGNORECASE)
        text = match.group(1) if match else full_text

    # 1. Unique RSK-01 / RISK-01 IDs
    rsk_ids = set(re.findall(r"\b(?:RSK|RISK)[-‑_]?\d+\b", text, re.IGNORECASE))
    if len(rsk_ids) >= 1:
        return len(rsk_ids)

    # 2. Table rows in Risk section
    risk_table_rows = [
        line for line in text.split("\n")
        if line.strip().startswith("|")
        and not re.search(r"\|\s*[-:]+[-| :]+\|", line)
        and not re.search(r"(?i)\|\s*(?:Risk\s*ID|ID|Category|Description)\s*\|", line)
    ]
    if len(risk_table_rows) >= 1:
        return len(risk_table_rows)

    return 0


def calculate_prd_metrics(full_text: str) -> Dict[str, Any]:
    """
    Dynamically analyze the generated PRD to compute genuine quality and completeness metrics.
    Directly evaluated from the 6 required PRD components:
    1. Problem Statement & Scope
    2. User Personas
    3. User Stories & Acceptance Criteria
    4. Functional Requirements
    5. Non-Functional Requirements (5 dimensions)
    6. Risk Assessment Matrix
    """
    if not full_text or not full_text.strip():
        return {
            "word_count": 0,
            "read_time_min": 0,
            "persona_count": 0,
            "story_count": 0,
            "fr_count": 0,
            "risk_count": 0,
            "completeness_score": 0,
            "covered_sections": []
        }

    words = len(full_text.split())
    estimated_read_time_min = max(1, round(words / 200)) if words > 0 else 0
    sections = extract_sections(full_text)

    # Count individual items dynamically
    story_count = count_user_stories(full_text, sections.get("User Stories", ""))
    fr_count = count_functional_requirements(full_text, sections.get("Functional Requirements", ""))
    risk_count = count_risks(full_text, sections.get("Risk Matrix", ""))

    persona_text = sections.get("Personas", "") or full_text
    persona_matches = re.findall(r"(?:^|\n)#{2,4}\s*(?:Persona\s*\d+|Persona:)", persona_text, re.IGNORECASE)
    persona_count = max(len(persona_matches), len(re.findall(r"\bPersona\s*\d+:\s*[A-Z]", persona_text)))
    if persona_count == 0 and ("persona" in persona_text.lower() and len(persona_text.strip()) > 50):
        persona_count = 2

    # Calculate Completeness Score (0% - 100%) purely across the 6 required components:
    # 1. Problem & Scope (Weight: 1/6)
    score_problem = 0.0
    if len(sections.get("Problem Statement", "").strip()) > 50:
        score_problem += 0.5
    if len(sections.get("Scope & Boundaries", "").strip()) > 30 or len(sections.get("Executive Summary", "").strip()) > 50:
        score_problem += 0.5

    # 2. Personas (Weight: 1/6)
    score_personas = min(1.0, persona_count / 2.0)

    # 3. User Stories (Weight: 1/6)
    score_stories = min(1.0, story_count / 4.0)

    # 4. Functional Requirements (Weight: 1/6)
    score_fr = min(1.0, fr_count / 5.0)

    # 5. Non-Functional Requirements (Weight: 1/6)
    nfr_text = sections.get("Non-Functional Requirements", "").lower()
    nfr_dimensions = ["performance", "scalability", "security", "usability", "reliability"]
    found_nfr = sum(1 for dim in nfr_dimensions if dim in nfr_text)
    score_nfr = found_nfr / 5.0 if len(nfr_text) > 30 else 0.0

    # 6. Risk Assessment (Weight: 1/6)
    score_risks = min(1.0, risk_count / 4.0)

    total_component_score = (score_problem + score_personas + score_stories + score_fr + score_nfr + score_risks) / 6.0
    completeness_score = min(100, max(0, round(total_component_score * 100)))

    covered_sections = [k for k, v in sections.items() if len(v.strip()) > 20]

    return {
        "word_count": words,
        "read_time_min": estimated_read_time_min,
        "persona_count": persona_count,
        "story_count": story_count,
        "fr_count": fr_count,
        "risk_count": risk_count,
        "completeness_score": completeness_score,
        "covered_sections": covered_sections
    }


def export_as_html(markdown_text: str, title: str = "Product Requirement Document") -> str:
    """Generate a clean, standalone, printable HTML document from Markdown."""
    import html
    escaped = html.escape(markdown_text)

    # Basic regex formatting for headers, bold, code, tables
    html_body = escaped
    html_body = re.sub(r'# (.*?)\n', r'<h1>\1</h1>\n', html_body)
    html_body = re.sub(r'## (.*?)\n', r'<h2>\1</h2>\n', html_body)
    html_body = re.sub(r'### (.*?)\n', r'<h3>\1</h3>\n', html_body)
    html_body = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html_body)
    html_body = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html_body)
    html_body = re.sub(r'`(.*?)`', r'<code>\1</code>', html_body)
    html_body = re.sub(r'\n---', r'<hr/>', html_body)
    html_body = html_body.replace('\n', '<br/>\n')

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(title)}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #1F2937;
            max-width: 900px;
            margin: 40px auto;
            padding: 0 20px;
            background-color: #FFFFFF;
        }}
        h1 {{ color: #1E3A8A; border-bottom: 2px solid #DBEAFE; padding-bottom: 8px; margin-top: 30px; }}
        h2 {{ color: #1E40AF; margin-top: 24px; }}
        h3 {{ color: #374151; }}
        code {{ background-color: #F3F4F6; padding: 2px 6px; border-radius: 4px; font-family: monospace; font-size: 0.9em; }}
        hr {{ border: 0; height: 1px; background: #E5E7EB; margin: 30px 0; }}
        @media print {{
            body {{ max-width: 100%; margin: 0; }}
        }}
    </style>
</head>
<body>
    {html_body}
</body>
</html>
"""
    return html_template


def export_as_json(prd_data: Dict[str, Any]) -> str:
    """Export PRD data as formatted JSON."""
    return json.dumps(prd_data, indent=2)
