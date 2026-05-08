"""
LLM Analyzer Module
Sends document text to Groq API and returns structured JSON analysis.
Uses the official 'groq' Python SDK (OpenAI-compatible interface).
"""

import json
import re
from groq import Groq


# Best free model on Groq — fast, accurate, large context
GROQ_MODEL = "llama-3.3-70b-versatile"


def build_analysis_prompt(document_text: str) -> str:
    """
    Build a structured system + user prompt that instructs the LLM
    to return a clean JSON analysis of the education regulation document.
    """
    system_prompt = (
        "You are an expert Education Policy Analyst specializing in Indian higher "
        "education regulations issued by UGC, AICTE, NAAC, NIRF, and the Ministry "
        "of Education. Always respond with STRICTLY VALID JSON only. "
        "Do NOT include markdown, code fences, or any text outside the JSON object."
    )

    user_prompt = f"""Analyze the following education regulation document and return ONLY a valid JSON object.

DOCUMENT TEXT:
\"\"\"
{document_text}
\"\"\"

Return ONLY the following JSON structure with all fields filled accurately:

{{
  "document_title": "Exact or inferred title of the document",
  "issuing_body": "UGC / AICTE / NAAC / NIRF / Ministry of Education / Other",
  "topic_category": "One of: Accreditation | Scholarship | Curriculum | Faculty Policy | Examination | Admissions | Ranking | Infrastructure | Research | Other",
  "regulation_date": "Date if mentioned, else 'Not specified'",
  "purpose": "2-3 sentences explaining what this regulation proposes or changes",
  "background": "Historical context and why this regulation was introduced",
  "summary": "Easy-to-read 10-15 line summary for students, faculty, and administrators",
  "stakeholder_impact": {{
    "students": {{
      "impact_level": "Positive | Negative | Neutral | Mixed",
      "details": "Specific impact on students"
    }},
    "faculty": {{
      "impact_level": "Positive | Negative | Neutral | Mixed",
      "details": "Specific impact on faculty members"
    }},
    "institutions": {{
      "impact_level": "Positive | Negative | Neutral | Mixed",
      "details": "Specific impact on colleges and universities"
    }},
    "administrators": {{
      "impact_level": "Positive | Negative | Neutral | Mixed",
      "details": "Specific impact on academic administrators"
    }},
    "accreditation_teams": {{
      "impact_level": "Positive | Negative | Neutral | Mixed",
      "details": "Specific impact on NAAC/accreditation bodies"
    }}
  }},
  "impact_assessment": {{
    "short_term": ["Impact 1 (0-1 year)", "Impact 2", "Impact 3"],
    "medium_term": ["Impact 1 (1-5 years)", "Impact 2", "Impact 3"],
    "long_term": ["Impact 1 (>5 years)", "Impact 2", "Impact 3"]
  }},
  "positives": ["Benefit 1", "Benefit 2", "Benefit 3"],
  "negatives": ["Drawback 1", "Drawback 2", "Drawback 3"],
  "risks": ["Risk 1", "Risk 2", "Risk 3"],
  "opportunities": ["Opportunity 1", "Opportunity 2", "Opportunity 3"],
  "compliance_requirements": ["Requirement 1", "Requirement 2"],
  "compliance_burden": "Estimation of administrative hours and legal overhead required for institutional adoption",
  "fiscal_metrics": "Mapping of immediate implementation expenses vs long-term operational cost-benefit ratios",
  "equity_metrics": "Assessment of potential disparate impacts on vulnerable student demographics",
  "academic_quality": "Measurable shifts in student learning outcomes and curriculum efficacy",
  "execution_framework": {{
    "problem_definition": "The exact policy goals and baseline constraints",
    "stakeholder_mapping": "Downstream effects across students, staff, and partners",
    "cost_benefit_analysis": "Quantification of hard financial and soft social benefits",
    "risk_assessment": "Legal friction points and technological dependencies"
  }},
  "chronology_notes": "A detailed timeline and list of related historical circulars, previous amendments, and foundational policies (e.g., NEP 2020, NPE 1986, AICTE Act 1987) that provide context for this regulation. Even if not explicitly mentioned in the text, use your internal knowledge of the Indian regulatory ecosystem to provide a complete historical background.",
  "sentiment": "Positive | Negative | Neutral | Mixed",
  "risk_level": "Low | Medium | High",
  "key_clauses": ["Important clause 1", "Important clause 2", "Important clause 3"]
}}"""

    return system_prompt, user_prompt


def analyze_document(document_text: str, api_key: str) -> dict:
    """
    Send document text to Groq API and return structured analysis.

    Args:
        document_text: Extracted text from the regulation document
        api_key: Groq API key (starts with gsk_...)

    Returns:
        dict: Parsed JSON analysis result
    """
    client = Groq(api_key=api_key)

    system_prompt, user_prompt = build_analysis_prompt(document_text)

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        temperature=0.2,       # Low temperature → factual, consistent output
        max_tokens=4096,
        top_p=0.8,
    )

    raw_output = response.choices[0].message.content.strip()
    return parse_llm_response(raw_output)


def parse_llm_response(raw_output: str) -> dict:
    """
    Safely parse the LLM's JSON output.
    Handles cases where the model wraps output in markdown code fences.

    Args:
        raw_output: Raw string output from the LLM

    Returns:
        dict: Parsed analysis dictionary
    """
    # Strip markdown code fences if present  (```json ... ```)
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw_output, flags=re.MULTILINE)
    cleaned = re.sub(r"\s*```$",          "", cleaned,    flags=re.MULTILINE)
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)

    except json.JSONDecodeError as e:
        # Fallback: extract the first {...} block using regex
        json_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        raise ValueError(
            f"Failed to parse LLM response as JSON.\n"
            f"Parse error: {str(e)}\n"
            f"Raw output (first 500 chars): {raw_output[:500]}"
        )
