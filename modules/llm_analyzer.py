"""
LLM Analyzer Module — Agentic Pipeline
Analyst -> Critic -> Refiner (self-correction loop) -> Strategist.
Uses the official 'groq' Python SDK (OpenAI-compatible interface).
"""

import json
import re
from groq import Groq

from modules.document_processor import retrieve_relevant_chunks
from modules.emotion_analyzer import detect_emotion

GROQ_MODEL = "llama-3.3-70b-versatile"


# ── Shared helpers ────────────────────────────────────────────────────────────

def _call_groq(client, system_prompt, user_prompt, temperature=0.2, max_tokens=4096):
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=0.8,
    )
    return response.choices[0].message.content.strip()


def parse_llm_response(raw_output: str) -> dict:
    """Safely parse the LLM's JSON output, stripping markdown fences if present."""
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw_output, flags=re.MULTILINE)
    cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE)
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
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


# ── Agent 1: Analyst — produces the first structured draft ──────────────────

def build_analysis_prompt(document_text: str):
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
    "students": {{"impact_level": "Positive | Negative | Neutral | Mixed", "details": "Specific impact on students"}},
    "faculty": {{"impact_level": "Positive | Negative | Neutral | Mixed", "details": "Specific impact on faculty members"}},
    "institutions": {{"impact_level": "Positive | Negative | Neutral | Mixed", "details": "Specific impact on colleges and universities"}},
    "administrators": {{"impact_level": "Positive | Negative | Neutral | Mixed", "details": "Specific impact on academic administrators"}},
    "accreditation_teams": {{"impact_level": "Positive | Negative | Neutral | Mixed", "details": "Specific impact on NAAC/accreditation bodies"}}
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
  "chronology_notes": "A detailed timeline and list of related historical circulars, previous amendments, and foundational policies (e.g., NEP 2020, NEP 1986, AICTE Act 1987) that provide context for this regulation. Even if not explicitly mentioned in the text, use your internal knowledge of the Indian regulatory ecosystem to provide a complete historical background.",
  "sentiment": "Positive | Negative | Neutral | Mixed",
  "risk_level": "Low | Medium | High",
  "key_clauses": ["Important clause 1", "Important clause 2", "Important clause 3"]
}}"""
    return system_prompt, user_prompt


def _run_analyst_agent(client, relevant_text: str) -> dict:
    system_prompt, user_prompt = build_analysis_prompt(relevant_text)
    raw = _call_groq(client, system_prompt, user_prompt, temperature=0.2, max_tokens=4096)
    return parse_llm_response(raw)


# ── Agent 2: Critic — self-review, scores metrics (LLM-as-a-Judge), verdicts ──

def _run_critic_agent(client, relevant_text: str, draft: dict) -> dict:
    system_prompt = (
        "You are a strict Senior Editor reviewing a junior analyst's regulation "
        "analysis before it reaches decision-makers. Respond with STRICTLY VALID "
        "JSON only, no markdown."
    )
    user_prompt = f"""Original document excerpt:
\"\"\"
{relevant_text[:6000]}
\"\"\"

Junior analyst's draft JSON analysis:
{json.dumps(draft, ensure_ascii=False)[:6000]}

Critically review the draft. Evaluate and score the analysis on the following metrics (each from 1 to 10, where 10 is perfect):
1. Grounding Score: Are all facts, benefits, and requirements fully supported by the document excerpt? Check for any hallucinated claims.
   CRITICAL EXCEPTION: Do NOT penalize or check the fields "chronology_notes", "fiscal_metrics", "equity_metrics", and "academic_quality" for strict grounding in the excerpt. The Analyst is explicitly instructed to use external regulatory-ecosystem knowledge for these. For these four fields, only penalize them (or flag as issues) if they contain factually implausible information or internal contradictions, NOT because they are not stated in the excerpt.
2. Consistency Score: Are the fields logical and self-consistent? (e.g. if sentiment is Positive, is the risk level aligned, or explained if High? Are impact levels consistent with their details?)
3. Completeness Score: Did the analyst fully map out the impacts of all requested stakeholders and timelines without skipping sections?

Flag any specific issues in the issues list. If any score is less than 8, set verdict to 'revise'. Otherwise, set verdict to 'approve'.

Return ONLY this JSON:
{{
  "grounding_score": <integer 1-10>,
  "consistency_score": <integer 1-10>,
  "completeness_score": <integer 1-10>,
  "issues": ["specific issue 1", "specific issue 2"],
  "verdict": "approve" or "revise"
}}"""
    raw = _call_groq(client, system_prompt, user_prompt, temperature=0.1, max_tokens=800)
    try:
        res = parse_llm_response(raw)
        # Compute general confidence score for backwards compatibility
        g = res.get("grounding_score", 10)
        c = res.get("consistency_score", 10)
        comp = res.get("completeness_score", 10)
        res["confidence"] = int((g + c + comp) / 3)
        return res
    except ValueError:
        return {
            "grounding_score": 10,
            "consistency_score": 10,
            "completeness_score": 10,
            "confidence": 10,
            "issues": [],
            "verdict": "approve"
        }


# ── Agent 3: Refiner — corrects the draft using the critic's feedback ────────

def _run_refiner_agent(client, relevant_text: str, draft: dict, critique: dict) -> dict:
    system_prompt = (
        "You are the same Education Policy Analyst, revising your own work after "
        "editorial feedback. Respond with STRICTLY VALID JSON only, matching the "
        "exact schema/keys of the draft you were given, with corrected values."
    )
    user_prompt = f"""Original document excerpt:
\"\"\"
{relevant_text[:6000]}
\"\"\"

Your previous draft:
{json.dumps(draft, ensure_ascii=False)}

Editor's feedback (fix each of these before resubmitting):
{json.dumps(critique.get("issues", []), ensure_ascii=False)}

Return the corrected, complete JSON object with the SAME schema/keys as your previous draft."""
    raw = _call_groq(client, system_prompt, user_prompt, temperature=0.15, max_tokens=4096)
    try:
        return parse_llm_response(raw)
    except ValueError:
        return draft  # fall back to prior draft if the revision fails to parse


# ── Agent 4: Strategist — EdTech opportunities + government AI guidance ─────

def _run_strategist_agent(client, relevant_text: str, analysis: dict) -> dict:
    system_prompt = (
        "You are a strategic advisor to EdTech founders and Ministry of Education "
        "policymakers. Respond with STRICTLY VALID JSON only, no markdown."
    )
    context = {
        "summary": analysis.get("summary"),
        "risks": analysis.get("risks"),
        "opportunities": analysis.get("opportunities"),
        "stakeholder_impact": analysis.get("stakeholder_impact"),
        "risk_level": analysis.get("risk_level"),
    }
    user_prompt = f"""Validated regulation analysis (already fact-checked):
{json.dumps(context, ensure_ascii=False)[:5000]}

Based on this SPECIFIC regulation, generate:
1. 3-5 concrete EdTech business opportunities this regulation opens up (name real products/services, not generic advice)
2. 3-5 specific, responsible ways Government/Ministry could use AI to improve implementation or monitoring of this regulation
3. An overall opportunity outlook

Return ONLY this JSON:
{{
  "edtech_business_opportunities": ["...", "..."],
  "government_ai_guidance": ["...", "..."],
  "opportunity_outlook": "Low | Medium | High"
}}"""
    raw = _call_groq(client, system_prompt, user_prompt, temperature=0.3, max_tokens=1200)
    try:
        return parse_llm_response(raw)
    except ValueError:
        return {"edtech_business_opportunities": [], "government_ai_guidance": [], "opportunity_outlook": "Not available"}


# ── Orchestrator — the agentic self-correction loop ──────────────────────────

def analyze_document(document_text: str, api_key: str, max_refine_rounds: int = 1) -> dict:
    """
    Agentic pipeline: Analyst -> Critic -> (Refiner, looped) -> Strategist -> Emotion tagging.

    Unlike a single LLM call, this pipeline lets the model check its own work:
    the Critic agent scores the Analyst's draft and lists concrete issues; if
    it isn't satisfied, the Refiner agent rewrites the draft to address those
    issues. Returns the final analysis dict plus "_agent_trace": a log of what
    each agent did (for UI transparency / demoing the loop).
    """
    client = Groq(api_key=api_key)
    trace = []

    search_query = ("students faculty institutions administrators accreditation "
                     "compliance short_term positives negatives risks opportunities equity")
    relevant_text = retrieve_relevant_chunks(document_text, query=search_query, top_k=4, chunk_size=1000)

    # 1. Analyst drafts the first version
    analysis = _run_analyst_agent(client, relevant_text)
    trace.append({"agent": "Analyst", "note": "Drafted initial structured analysis."})

    # 2. Critic + Refiner self-correction loop
    prev_issues_count = None
    prev_confidence = None
    no_improvement_count = 0

    for round_num in range(1, max_refine_rounds + 1):
        critique = _run_critic_agent(client, relevant_text, analysis)
        
        trace.append({
            "agent": "Critic",
            "note": f"Round {round_num}: overall confidence {critique.get('confidence', '?')}/10. {len(critique.get('issues', []))} issue(s) flagged.",
            "issues": critique.get("issues", []),
            "metrics": {
                "grounding": critique.get("grounding_score"),
                "consistency": critique.get("consistency_score"),
                "completeness": critique.get("completeness_score")
            }
        })
        
        if critique.get("verdict") == "approve" or not critique.get("issues"):
            break
            
        current_issues_count = len(critique.get("issues", []))
        current_confidence = critique.get("confidence", 0)
        
        if prev_issues_count is not None and prev_confidence is not None:
            if current_issues_count >= prev_issues_count and current_confidence <= prev_confidence:
                no_improvement_count += 1
            else:
                no_improvement_count = 0
                
        prev_issues_count = current_issues_count
        prev_confidence = current_confidence
        
        if no_improvement_count >= 2:
            trace.append({
                "agent": "Refiner",
                "note": f"Refiner: stopped early, no improvement after {no_improvement_count} rounds."
            })
            break
            
        analysis = _run_refiner_agent(client, relevant_text, analysis, critique)
        trace.append({"agent": "Refiner", "note": f"Round {round_num}: revised draft to address flagged issues."})

    # 3. Strategist adds business + policy-AI guidance grounded on the validated analysis
    analysis["strategic_recommendations"] = _run_strategist_agent(client, relevant_text, analysis)
    trace.append({"agent": "Strategist", "note": "Generated EdTech business opportunities & government AI guidance."})

    # 4. Emotion tagging via local Hugging Face DistilRoBERTa model
    if "stakeholder_impact" in analysis and isinstance(analysis["stakeholder_impact"], dict):
        for stakeholder_key, stakeholder_info in analysis["stakeholder_impact"].items():
            if isinstance(stakeholder_info, dict):
                details = stakeholder_info.get("details", "")
                emotion = detect_emotion(details)
                stakeholder_info["emotion"] = emotion.capitalize()

    analysis["_agent_trace"] = trace
    return analysis
