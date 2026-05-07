"""
ERIA - Education Regulation Impact Analyzer
Main Streamlit Dashboard Application

Author: GUVI Capstone Project
Standard: PEP 8
"""

import os
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from dotenv import load_dotenv

from modules.document_processor import (
    extract_text_from_pdf,
    extract_text_from_url,
    truncate_text,
)
from modules.llm_analyzer import analyze_document, GROQ_MODEL
from modules.report_generator import generate_pdf_report

# ── Load environment variables ────────────────────────────────────────────────
load_dotenv()

# ── Page Configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ERIA – Education Regulation Impact Analyzer",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

  /* ── Global ── */
  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
  .stApp { background: #0b1120; color: #e2e8f0; }

  /* ── Hero Banner ── */
  .hero {
    background: linear-gradient(135deg, #1e3a8a 0%, #1d4ed8 50%, #7c3aed 100%);
    border-radius: 16px;
    padding: 40px 32px;
    margin-bottom: 24px;
    text-align: center;
  }
  .hero h1 { font-size: 2.4rem; font-weight: 700; color: #fff; margin: 0; }
  .hero p  { font-size: 1.05rem; color: #bfdbfe; margin-top: 8px; }

  /* ── Cards ── */
  .card {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 16px;
  }
  .card-title {
    font-size: 1.05rem;
    font-weight: 600;
    color: #93c5fd;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  /* ── Badge ── */
  .badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-left: 8px;
  }
  .badge-positive { background: #14532d; color: #86efac; }
  .badge-negative { background: #450a0a; color: #fca5a5; }
  .badge-mixed    { background: #451a03; color: #fcd34d; }
  .badge-neutral  { background: #1e293b; color: #94a3b8; border: 1px solid #475569; }

  /* ── Risk pills ── */
  .risk-low    { background: #14532d; color: #86efac; padding: 4px 14px; border-radius: 9999px; font-weight: 700; font-size: 0.85rem; }
  .risk-medium { background: #451a03; color: #fcd34d; padding: 4px 14px; border-radius: 9999px; font-weight: 700; font-size: 0.85rem; }
  .risk-high   { background: #450a0a; color: #fca5a5; padding: 4px 14px; border-radius: 9999px; font-weight: 700; font-size: 0.85rem; }

  /* ── Timeline ── */
  .timeline-item {
    border-left: 3px solid #3b82f6;
    padding-left: 16px;
    margin-bottom: 12px;
    position: relative;
  }
  .timeline-dot {
    width: 10px; height: 10px;
    background: #3b82f6;
    border-radius: 50%;
    position: absolute;
    left: -6.5px; top: 4px;
  }

  /* ── Sidebar ── */
  section[data-testid="stSidebar"] {
    background: #0f172a;
    border-right: 1px solid #1e293b;
  }

  /* ── Tabs ── */
  .stTabs [data-baseweb="tab-list"] {
    background: #1e293b;
    border-radius: 10px;
    padding: 4px;
    gap: 4px;
  }
  .stTabs [data-baseweb="tab"] {
    background: transparent;
    color: #94a3b8;
    border-radius: 8px;
    font-size: 0.9rem;
    padding: 8px 16px;
  }
  .stTabs [aria-selected="true"] {
    background: #1d4ed8 !important;
    color: #fff !important;
  }

  /* ── Buttons ── */
  .stButton > button {
    background: linear-gradient(135deg, #1d4ed8, #7c3aed);
    color: white;
    border: none;
    border-radius: 10px;
    padding: 10px 24px;
    font-weight: 600;
    font-size: 0.95rem;
    transition: transform 0.2s, box-shadow 0.2s;
    width: 100%;
  }
  .stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(29, 78, 216, 0.4);
  }

  /* ── Metric boxes ── */
  [data-testid="stMetricValue"] { color: #93c5fd; font-weight: 700; }
  [data-testid="stMetricLabel"] { color: #64748b; }

  /* ── Divider ── */
  hr { border-color: #1e293b; }

  /* ── Bullet lists ── */
  .bullet-item {
    padding: 6px 0 6px 16px;
    border-left: 2px solid #3b82f6;
    margin-bottom: 6px;
    color: #cbd5e1;
    font-size: 0.93rem;
  }
  /* ── Plotly Background ── */
  .js-plotly-plot .plotly .main-svg { background: transparent !important; }
</style>
""", unsafe_allow_html=True)


# ── Helper render functions ───────────────────────────────────────────────────

def impact_badge(level: str) -> str:
    """Return HTML badge string for an impact level."""
    cls_map = {
        "Positive": "badge-positive",
        "Negative": "badge-negative",
        "Mixed":    "badge-mixed",
        "Neutral":  "badge-neutral",
    }
    css_class = cls_map.get(level, "badge-neutral")
    return f'<span class="badge {css_class}">{level}</span>'


def risk_pill(level: str) -> str:
    """Return HTML pill for risk level."""
    cls_map = {
        "Low":    "risk-low",
        "Medium": "risk-medium",
        "High":   "risk-high",
    }
    css_class = cls_map.get(level, "risk-medium")
    return f'<span class="{css_class}">{level} Risk</span>'


def render_risk_gauge(level: str) -> None:
    """Render a Plotly gauge chart for risk level."""
    values = {"Low": 25, "Medium": 50, "High": 85}
    val = values.get(level, 50)
    colors = {"Low": "#22c55e", "Medium": "#f59e0b", "High": "#ef4444"}
    color = colors.get(level, "#f59e0b")

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=val,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': f"Risk Level: {level}", 'font': {'size': 18, 'color': color}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#475569"},
            'bar': {'color': color},
            'bgcolor': "#1e293b",
            'borderwidth': 2,
            'bordercolor': "#334155",
            'steps': [
                {'range': [0, 40], 'color': 'rgba(34, 197, 94, 0.1)'},
                {'range': [40, 70], 'color': 'rgba(245, 158, 11, 0.1)'},
                {'range': [70, 100], 'color': 'rgba(239, 68, 68, 0.1)'}
            ],
        }
    ))
    fig.update_layout(
        height=250, margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font={'color': "#94a3b8"}
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})


def render_impact_chart(stakeholders: dict) -> None:
    """Render a Plotly bar chart for stakeholder impacts."""
    categories = []
    scores = []
    color_map = {"Positive": "#22c55e", "Mixed": "#f59e0b", "Neutral": "#64748b", "Negative": "#ef4444"}
    colors = []

    label_map = {
        "students": "Students",
        "faculty": "Faculty",
        "institutions": "Institutions",
        "administrators": "Admins",
        "accreditation_teams": "Accreditation"
    }

    score_map = {"Positive": 1, "Mixed": 0.5, "Neutral": 0, "Negative": -1}

    for key, label in label_map.items():
        if key in stakeholders:
            level = stakeholders[key].get("impact_level", "Neutral")
            categories.append(label)
            scores.append(score_map.get(level, 0))
            colors.append(color_map.get(level, "#64748b"))

    fig = go.Figure(go.Bar(
        x=categories,
        y=scores,
        marker_color=colors,
        text=categories,
        textposition='auto',
    ))

    fig.update_layout(
        title={'text': "Stakeholder Sentiment Map", 'font': {'size': 16, 'color': '#93c5fd'}},
        height=250, margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(showticklabels=False, range=[-1.2, 1.2], zeroline=True, zerolinecolor="#334155"),
        xaxis=dict(showticklabels=True, tickfont=dict(size=10)),
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})


def render_bullet_list(items: list) -> None:
    """Render a styled bullet list using custom HTML."""
    for item in items:
        st.markdown(f'<div class="bullet-item">• {item}</div>', unsafe_allow_html=True)


def render_summary_tab(analysis: dict) -> None:
    """Render the Executive Summary tab."""
    # Row 1: Document Info & Gauge
    c1, c2 = st.columns([1, 1.2])
    with c1:
        st.markdown(f"""
        <div class="card" style="height: 250px; overflow-y: auto;">
          <div class="card-title">📋 Document Overview</div>
          <table style="width:100%; color:#cbd5e1; font-size:0.9rem; border-collapse:collapse;">
            <tr><td style="padding:6px; color:#64748b; width:140px;">Issuing Body</td>
                <td style="padding:6px; font-weight:600; color:#93c5fd;">{analysis.get('issuing_body','N/A')}</td></tr>
            <tr><td style="padding:6px; color:#64748b;">Category</td>
                <td style="padding:6px; font-weight:600;">{analysis.get('topic_category','N/A')}</td></tr>
            <tr><td style="padding:6px; color:#64748b;">Regulation Date</td>
                <td style="padding:6px;">{analysis.get('regulation_date','Not specified')}</td></tr>
            <tr><td style="padding:6px; color:#64748b;">Sentiment</td>
                <td style="padding:6px;">{impact_badge(analysis.get('sentiment','Neutral'))}</td></tr>
          </table>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="card" style="height: 250px;">', unsafe_allow_html=True)
        render_risk_gauge(analysis.get("risk_level", "Medium"))
        st.markdown('</div>', unsafe_allow_html=True)

    # Row 2: Summary & Sentiment Chart
    c3, c4 = st.columns([1.5, 1])
    with c3:
        st.markdown('<div class="card" style="height: 250px; overflow-y: auto;"><div class="card-title">📝 Executive Summary</div>', unsafe_allow_html=True)
        st.markdown(f'<p style="color:#cbd5e1; line-height:1.6; font-size:0.95rem;">{analysis.get("summary","")}</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with c4:
        st.markdown('<div class="card" style="height: 250px;">', unsafe_allow_html=True)
        render_impact_chart(analysis.get("stakeholder_impact", {}))
        st.markdown('</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="card"><div class="card-title">🎯 Purpose</div>', unsafe_allow_html=True)
        st.markdown(f'<p style="color:#cbd5e1; line-height:1.7;">{analysis.get("purpose","")}</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card"><div class="card-title">🕰️ Historical Background</div>', unsafe_allow_html=True)
        st.markdown(f'<p style="color:#cbd5e1; line-height:1.7;">{analysis.get("background","")}</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    key_clauses = analysis.get("key_clauses", [])
    if key_clauses:
        st.markdown('<div class="card"><div class="card-title">📌 Key Clauses</div>', unsafe_allow_html=True)
        render_bullet_list(key_clauses)
        st.markdown('</div>', unsafe_allow_html=True)


def render_stakeholder_tab(analysis: dict) -> None:
    """Render the Stakeholder Impact tab."""
    stakeholders = analysis.get("stakeholder_impact", {})
    icons = {
        "students":           ("🎓", "Students"),
        "faculty":            ("👩‍🏫", "Faculty"),
        "institutions":       ("🏛️", "Institutions"),
        "administrators":     ("🗂️", "Administrators"),
        "accreditation_teams": ("✅", "Accreditation Teams"),
    }

    for key, (icon, label) in icons.items():
        data = stakeholders.get(key, {})
        level = data.get("impact_level", "Neutral")
        details = data.get("details", "No details available.")
        st.markdown(f"""
        <div class="card">
          <div class="card-title">{icon} {label} {impact_badge(level)}</div>
          <p style="color:#cbd5e1; line-height:1.7; margin:0;">{details}</p>
        </div>
        """, unsafe_allow_html=True)


def render_impact_tab(analysis: dict) -> None:
    """Render the Impact Assessment tab."""
    impact = analysis.get("impact_assessment", {})

    cols = st.columns(3)
    config = [
        ("short_term",  "⚡ Short-Term",   "0–1 Year",   "#3b82f6"),
        ("medium_term", "📈 Medium-Term",  "1–5 Years",  "#8b5cf6"),
        ("long_term",   "🌐 Long-Term",    ">5 Years",   "#06b6d4"),
    ]

    for col, (key, title, period, color) in zip(cols, config):
        with col:
            items = impact.get(key, [])
            st.markdown(f"""
            <div class="card" style="border-top: 3px solid {color};">
              <div class="card-title" style="color:{color};">{title}</div>
              <div style="color:#64748b; font-size:0.8rem; margin-bottom:12px;">{period}</div>
            """, unsafe_allow_html=True)
            for item in items:
                st.markdown(f'<div class="bullet-item">• {item}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)


def render_risks_tab(analysis: dict) -> None:
    """Render the Risks & Opportunities tab."""
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="card" style="border-top:3px solid #22c55e;">'
                    '<div class="card-title" style="color:#22c55e;">✅ Positives</div>', unsafe_allow_html=True)
        render_bullet_list(analysis.get("positives", []))
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="card" style="border-top:3px solid #3b82f6;">'
                    '<div class="card-title" style="color:#93c5fd;">🚀 Opportunities</div>', unsafe_allow_html=True)
        render_bullet_list(analysis.get("opportunities", []))
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card" style="border-top:3px solid #ef4444;">'
                    '<div class="card-title" style="color:#fca5a5;">❌ Negatives</div>', unsafe_allow_html=True)
        render_bullet_list(analysis.get("negatives", []))
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="card" style="border-top:3px solid #f59e0b;">'
                    '<div class="card-title" style="color:#fcd34d;">⚠️ Risks</div>', unsafe_allow_html=True)
        render_bullet_list(analysis.get("risks", []))
        st.markdown('</div>', unsafe_allow_html=True)

    compliance = analysis.get("compliance_requirements", [])
    if compliance:
        st.markdown('<div class="card">'
                    '<div class="card-title">📋 Compliance Requirements</div>', unsafe_allow_html=True)
        render_bullet_list(compliance)
        st.markdown('</div>', unsafe_allow_html=True)


def render_chronology_tab(analysis: dict) -> None:
    """Render the Chronology & Policy History tab."""
    notes = analysis.get("chronology_notes", "")
    st.markdown('<div class="card"><div class="card-title">🕰️ Policy Chronology & History</div>', unsafe_allow_html=True)
    if notes:
        st.markdown(f'<p style="color:#cbd5e1; line-height:1.7;">{notes}</p>', unsafe_allow_html=True)
    else:
        st.markdown('<p style="color:#64748b;">No chronology information was found in this document.</p>',
                    unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────

def render_sidebar() -> str:
    """Render sidebar and return the Gemini API key."""
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center; padding:16px 0;">
          <div style="font-size:2.5rem;">⚖️</div>
          <div style="font-size:1.1rem; font-weight:700; color:#93c5fd;">ERIA</div>
          <div style="font-size:0.75rem; color:#475569;">Education Regulation Impact Analyzer</div>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        st.markdown("### 🔑 Groq API Key")
        api_key = st.text_input(
            label="API Key",
            type="password",
            value=os.getenv("GROQ_API_KEY", ""),
            placeholder="gsk_...",
            help="Get your FREE key at https://console.groq.com",
            label_visibility="collapsed",
        )

        if not api_key:
            st.warning("⚠️ Enter your Groq API key to enable analysis.")

        st.divider()

        st.markdown("### 📚 Official Sources")
        sources = {
            "UGC Circulars":     "https://www.ugc.gov.in/Circulars",
            "UGC Regulations":   "https://www.ugc.gov.in/regulations",
            "UGC Notices":       "https://www.ugc.gov.in/Notices",
            "UGC Guidelines":    "https://www.ugc.gov.in/Guideline",
        }
        for name, url in sources.items():
            st.markdown(f"🔗 [{name}]({url})")

        st.divider()
        st.markdown('<div style="font-size:0.75rem; color:#475569; text-align:center;">Powered by Groq · LLaMA 3.3 70B</div>',
                    unsafe_allow_html=True)

    return api_key


# ── Main App ──────────────────────────────────────────────────────────────────

def main() -> None:
    """Main application entry point."""

    api_key = render_sidebar()

    # Hero Banner
    st.markdown("""
    <div class="hero">
      <h1>⚖️ Education Regulation Impact Analyzer</h1>
      <p>Upload any UGC · AICTE · NAAC · NIRF circular — get instant AI-powered policy insights</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Input Section ─────────────────────────────────────────────────────────
    input_tab, url_tab = st.tabs(["📁 Upload PDF", "🌐 Paste URL"])

    document_text = None
    source_label = ""

    with input_tab:
        uploaded_file = st.file_uploader(
            "Drop your PDF regulation document here",
            type=["pdf"],
            help="Upload any UGC, AICTE, NAAC, NIRF, or Ministry of Education PDF",
        )
        if uploaded_file:
            source_label = uploaded_file.name
            with st.spinner("📄 Extracting text from PDF..."):
                try:
                    document_text = extract_text_from_pdf(uploaded_file)
                    st.success(f"✅ Extracted {len(document_text):,} characters from **{uploaded_file.name}**")
                except ValueError as e:
                    st.error(str(e))

    with url_tab:
        url_input = st.text_input(
            "Enter the URL of an education regulation page or PDF",
            placeholder="https://www.ugc.gov.in/Circulars/...",
        )
        fetch_btn = st.button("🌐 Fetch & Analyze URL")
        if fetch_btn and url_input:
            source_label = url_input
            with st.spinner("🌐 Fetching content from URL..."):
                try:
                    document_text = extract_text_from_url(url_input)
                    st.success(f"✅ Fetched {len(document_text):,} characters from URL.")
                except ValueError as e:
                    st.error(str(e))

    # ── Analyze Button ────────────────────────────────────────────────────────
    if document_text:
        st.divider()
        col_btn, col_info = st.columns([1, 3])
        with col_btn:
            analyze_btn = st.button("🔍 Analyze Regulation", use_container_width=True)
        with col_info:
            st.info(
                f"📊 Document ready: **{len(document_text):,}** characters | "
                f"Model: **{GROQ_MODEL}**"
            )

        if analyze_btn:
            if not api_key:
                st.error("❌ Please enter your Groq API key in the sidebar.")
                return

            # Truncate to fit LLM context
            truncated_text = truncate_text(document_text, max_chars=12000)

            with st.spinner("🤖 Analyzing regulation with Groq LLaMA 3.3 70B... (this may take 10–20 seconds)"):
                try:
                    analysis = analyze_document(truncated_text, api_key)
                    st.session_state["analysis"] = analysis
                    st.session_state["source_label"] = source_label
                    st.success("✅ Analysis complete!")
                except Exception as e:
                    st.error(f"❌ Analysis failed: {str(e)}")
                    return

    # ── Results Section ───────────────────────────────────────────────────────
    if "analysis" in st.session_state:
        analysis = st.session_state["analysis"]
        title = analysis.get("document_title", "Regulation Document")

        st.divider()
        st.markdown(f"## 📊 Analysis: {title}")

        # Quick metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Issuing Body",    analysis.get("issuing_body", "N/A"))
        m2.metric("Topic Category",  analysis.get("topic_category", "N/A"))
        m3.metric("Sentiment",       analysis.get("sentiment", "N/A"))
        m4.metric("Risk Level",      analysis.get("risk_level", "N/A"))

        st.divider()

        # Result tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📋 Summary",
            "👥 Stakeholder Impact",
            "📈 Impact Assessment",
            "⚠️ Risks & Opportunities",
            "🕰️ Chronology",
        ])

        with tab1:
            render_summary_tab(analysis)

        with tab2:
            render_stakeholder_tab(analysis)

        with tab3:
            render_impact_tab(analysis)

        with tab4:
            render_risks_tab(analysis)

        with tab5:
            render_chronology_tab(analysis)

        # ── Download Report ───────────────────────────────────────────────────
        st.divider()
        st.markdown("### 📥 Download Analysis Report")
        col_dl, col_sp = st.columns([1, 3])
        with col_dl:
            try:
                pdf_bytes = generate_pdf_report(analysis)
                filename = (
                    f"ERIA_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                )
                st.download_button(
                    label="⬇️ Download PDF Report",
                    data=pdf_bytes,
                    file_name=filename,
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception as e:
                st.error(f"Report generation error: {str(e)}")

    else:
        # Placeholder when no analysis is run yet
        st.divider()
        st.markdown("""
        <div class="card" style="text-align:center; padding:48px;">
          <div style="font-size:3rem;">📄</div>
          <div style="font-size:1.1rem; color:#475569; margin-top:12px;">
            Upload a PDF or paste a URL above to begin analysis
          </div>
          <div style="font-size:0.85rem; color:#334155; margin-top:8px;">
            Supports UGC · AICTE · NAAC · NIRF · Ministry of Education documents
          </div>
        </div>
        """, unsafe_allow_html=True)


# ── Entry Point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
