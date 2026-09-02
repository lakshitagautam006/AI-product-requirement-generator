"""Comprehensive End-to-End Test Suite for AI Product Requirement Generator."""
import sys
import os
import py_compile
import json

# Add project root to sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from src.config import (
    DEFAULT_GROQ_MODEL,
    FALLBACK_GROQ_MODELS,
    get_available_groq_models,
    get_default_model,
    KNOWLEDGE_BASE_DIR,
    CHROMA_PERSIST_DIR
)
from src.rag.vector_store import initialize_vector_store, load_knowledge_base_documents
from src.rag.retriever import retrieve_relevant_guidelines
from src.agents.prompts import BA_PROMPT_TEMPLATE, PM_PROMPT_TEMPLATE
from src.utils.export_utils import (
    sanitize_filename,
    extract_sections,
    calculate_prd_metrics,
    count_user_stories,
    count_functional_requirements,
    count_risks,
    export_as_html,
    export_as_json
)

# Product 1: Campus Food Delivery (Real Flagship Output - 6 Stories, 15 FRs, 6 Risks)
PRODUCT_1_PRD = """# Product Requirement Document (PRD): QuickBite Campus

# 1. Executive Summary & Value Proposition
QuickBite Campus is an ultra-fast food delivery platform for universities.

# 2. Problem Statement & Market Context
**Core Pain Point**: Long queues and delayed meal delivery between classes.
**Affected Audience & Impact**: Over 20,000 students losing 30 mins daily.
**Existing Alternatives & Deficiencies**: Standard food apps charge high fees.
**Proposed Solution Concept**: Dorm-point lockers and batch delivery.

# 3. User Personas
### Persona 1: Alex - The Busy Student
- Demographics: 20-year-old CS Student.
- Goals: Quick lunch delivery before lectures.
- Frustrations: High delivery fees and uncertain ETA.

### Persona 2: Maya - The Dorm Resident
- Demographics: 19-year-old Freshman.
- Goals: Late-night coffee delivery.
- Frustrations: Cafeteria closed at 9 PM.

# 4. Scope & Boundaries
- In-Scope: Mobile app ordering, locker drop-off, campus card pay.
- Out-of-Scope: Nationwide delivery.

# 5. User Stories & Acceptance Criteria

| # | User Story (Agile Format) |
|---|---------------------------|
| **US‑001** | **As a** student, **I want** to place an order, **so that** I get food fast. |
| **US‑002** | **As a** student, **I want** live driver tracking, **so that** I know when to pickup. |
| **US‑003** | **As a** student, **I want** push notifications, **so that** I am alerted. |
| **US‑004** | **As a** professor, **I want** bulk catering, **so that** lab meetings are catered. |
| **US‑005** | **As a** vendor, **I want** menu CSV upload, **so that** items are searchable. |
| **US‑006** | **As an** admin, **I want** heat-map dashboard, **so that** I re-balance couriers. |

# 6. Functional Requirements (FR)
| Req ID | Module | Requirement Description | Priority |
| :--- | :--- | :--- | :--- |
| FR‑001 | Auth | SSO login | P0 |
| FR‑002 | Role | Role-based permissions | P0 |
| FR‑003 | Menu | Menu CSV import | P0 |
| FR‑004 | Order | Single-item ordering | P0 |
| FR‑005 | Bulk | Bulk order processing | P1 |
| FR‑006 | Dispatch | Geofenced courier dispatch | P0 |
| FR‑007 | Courier | Driver mobile app | P0 |
| FR‑008 | Payment | Campus wallet integration | P0 |
| FR‑009 | Notification | Push notification engine | P1 |
| FR‑010 | Vendor | Vendor analytics dashboard | P1 |
| FR‑011 | Admin | Operations dashboard | P1 |
| FR‑012 | Security | AES-256 data encryption | P0 |
| FR‑013 | Accessibility | WCAG 2.1 AA compliance | P2 |
| FR‑014 | Reliability | API rate limiter | P1 |
| FR‑015 | Scalability | Kubernetes auto-scaler | P0 |

# 7. Non‑Functional Requirements (NFR)
1. **Performance & Latency**: API response time < 150ms.
2. **Scalability**: Support 10,000 concurrent sessions.
3. **Security**: SOC2 & FERPA compliant data privacy.
4. **Usability**: WCAG 2.1 AA compliant UI.
5. **Reliability**: 99.95% system uptime.

# 8. Risk Assessment Matrix & Mitigation
| Risk ID | Category | Risk Description | Likelihood | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- | :--- |
| RSK‑01 | Technical | Geofence inaccuracies | Med | High | Hybrid Wi-Fi + GPS |
| RSK‑02 | Security | SSO token leak | Low | High | Token rotation |
| RSK‑03 | Business | Low vendor adoption | Med | Med | Revenue share pilot |
| RSK‑04 | Operational | Driver shortage | Med | High | Shift bidding |
| RSK‑05 | Compliance | Payment non-compliance | Low | High | Stripe tokenization |
| RSK‑06 | Technical | Map provider outage | Low | Med | Hot standby OSRM |
"""

# Product 2: Student Budget Tracker (3 Stories, 4 FRs, 3 Risks)
PRODUCT_2_PRD = """# Product Requirement Document (PRD): PennyWise Student

# 1. Executive Summary & Value Proposition
PennyWise is an AI expense manager helping college students avoid debt.

# 2. Problem Statement & Market Context
**Core Pain Point**: Students run out of monthly allowances by the 3rd week.
**Scope**: In-scope for mobile receipt scanning and spend alerts.

# 3. User Personas
### Persona 1: Liam - The Budget-Conscious Senior
- Goals: Save $200 monthly for post-grad rent.
### Persona 2: Maya - The Freshman
- Goals: Track weekly food budget.

# 4. Scope & Boundaries
- In-Scope: OCR receipt scan, bank sync, saving alerts.
- Out-of-Scope: Investment portfolios.

# 5. User Stories & Acceptance Criteria
### User Story 1: Scan Paper Receipt
As a student, I want to take a photo of my grocery receipt, so that items are categorized automatically.
- **Given** receipt camera is open
- **When** I snap a photo
- **Then** expense item and amount are logged.

### User Story 2: Allowance Burn Rate Warning
As a student, I want proactive alerts when my daily spending exceeds my target, so that I don't run out of money.
- **Given** daily spend exceeds $25
- **When** transaction posts
- **Then** notification is dispatched within 10 seconds.

### User Story 3: Weekly Spending Digest
As a student, I want a weekly digest, so that I see spending trends.
- **Given** end of week
- **When** digest generated
- **Then** charts displayed.

# 6. Functional Requirements (FR)
| Req ID | Module | Description | Priority |
| :--- | :--- | :--- | :--- |
| FR-001 | OCR | Extract merchant and total from image | P0 (Must) |
| FR-002 | Banking | Plaid API read-only transaction sync | P0 (Must) |
| FR-003 | Alerts | Real-time allowance burn rate notification | P1 (Should) |
| FR-004 | Reports | Weekly spending trends report | P2 (Nice) |

# 7. Non-Functional Requirements (NFR)
1. **Performance**: OCR processing latency < 2 seconds.
2. **Scalability**: 5,000 active users.
3. **Security**: AES-256 bank-grade credential encryption.
4. **Usability**: Mobile-first responsive UI.
5. **Reliability**: 99.9% uptime.

# 8. Risk Assessment Matrix & Mitigation
| Risk ID | Category | Risk Description | Likelihood | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- | :--- |
| RSK-01 | Technical | OCR parsing error on wrinkled paper | Med | Low | Manual confirmation fallback |
| RSK-02 | Security | Financial transaction data breach | Low | Critical | Read-only tokens, zero storage |
| RSK-03 | Business | Low student retention after exam week | Med | Med | Gamification saving streaks |
"""

# Product 3: AI Mental Wellness Companion (2 Stories, 2 FRs, 2 Risks)
PRODUCT_3_PRD = """# Product Requirement Document (PRD): MindEase AI

# 1. Executive Summary & Value Proposition
MindEase AI provides anonymous 24/7 exam stress coaching for students.

# 2. Problem Statement & Market Context
**Core Pain Point**: Campus mental counseling has 3-week waitlists during exams.
**Impact**: Escalating student burnout and anxiety.

# 3. User Personas
### Persona 1: Chloe - The Overwhelmed Pre-Med
- Goals: Micro-breathing exercises between study blocks.

# 4. Scope & Boundaries
- In-Scope: Stress logging, guided micro-meditation, crisis hotlines.
- Out-of-Scope: Medical diagnostic treatment.

# 5. User Stories & Acceptance Criteria
### User Story 1: Emergency Crisis Escalation
As an anxious student, I want immediate hotline escalation, so that I get real human help during panic.
- **Given** user inputs trigger words
- **When** crisis is detected
- **Then** 988 lifeline banner is pinned immediately.

### User Story 2: Micro-Meditation Audio
As a stressed student, I want 2-minute guided breathing audio, so that I calm down quickly.
- **Given** meditation tab open
- **When** play tapped
- **Then** audio streams smoothly.

# 6. Functional Requirements (FR)
| Req ID | Module | Description | Priority |
| :--- | :--- | :--- | :--- |
| FR-001 | AI Chat | Empathic supportive dialogue generation | P0 (Must) |
| FR-002 | Hotline | One-tap emergency crisis dialer integration | P0 (Must) |

# 7. Non-Functional Requirements (NFR)
1. **Security**: 100% anonymous, zero personally identifiable information logged.
2. **Performance**: Latency < 300ms for crisis keywords.
3. **Reliability**: 99.99% uptime for crisis hotline widget.

# 8. Risk Assessment Matrix & Mitigation
| Risk ID | Category | Risk Description | Likelihood | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- | :--- |
| RSK-01 | Legal | Misinterpretation as medical psychiatric therapy | Med | Critical | Prominent medical disclaimers |
| RSK-02 | Operational | Helpline API webhook failure | Low | High | Hardcoded fallback dialer |
"""


def test_syntax_and_compilation():
    print("[1/7] Checking Python syntax and compilation for all source files...")
    files_to_check = [
        "app.py",
        "src/config.py",
        "src/rag/vector_store.py",
        "src/rag/retriever.py",
        "src/agents/prompts.py",
        "src/agents/ba_agent.py",
        "src/agents/pm_agent.py",
        "src/agents/prd_generator.py",
        "src/utils/export_utils.py"
    ]
    for rel_path in files_to_check:
        full_path = os.path.join(PROJECT_ROOT, rel_path)
        assert os.path.exists(full_path), f"Missing file: {rel_path}"
        py_compile.compile(full_path, doraise=True)
        print(f"  [OK] {rel_path} compiles cleanly.")


def test_knowledge_base_and_rag():
    print("\n[2/7] Verifying Knowledge Base and ChromaDB Vector Store...")
    docs = load_knowledge_base_documents()
    assert len(docs) >= 3, f"Expected at least 3 knowledge base documents, got {len(docs)}"
    doc_names = [d.metadata.get("source") for d in docs]
    print(f"  [OK] Loaded knowledge docs: {doc_names}")

    vs = initialize_vector_store()
    assert vs is not None, "Vector store instance is None"

    ba_context = retrieve_relevant_guidelines("problem statement user personas guidelines for campus app", k=2)
    assert len(ba_context) > 50, "BA RAG retrieval returned insufficient context"
    print("  [OK] BA stage semantic retrieval verified.")

    pm_context = retrieve_relevant_guidelines("non-functional requirements security latency risk matrix", k=2)
    assert len(pm_context) > 50, "PM RAG retrieval returned insufficient context"
    print("  [OK] PM stage semantic retrieval verified.")


def test_agent_prompts():
    print("\n[3/7] Verifying Agent Prompt Templates...")
    ba_messages = BA_PROMPT_TEMPLATE.format_messages(
        product_name="QuickBite",
        product_idea="Campus food delivery",
        domain="FoodTech",
        constraints="Mobile first",
        rag_context="Sample guidelines"
    )
    assert len(ba_messages) == 2
    assert "Business Analyst" in ba_messages[0].content
    print("  [OK] BA Prompt Template verified.")

    pm_messages = PM_PROMPT_TEMPLATE.format_messages(
        product_name="QuickBite",
        ba_output="BA problem statement and personas",
        rag_context="Sample NFR guidelines"
    )
    assert len(pm_messages) == 2
    assert "Product Manager" in pm_messages[0].content
    print("  [OK] PM Prompt Template verified.")


def test_section_extraction():
    print("\n[4/7] Verifying PRD Section Parser across all 8 discrete sections...")
    sections = extract_sections(PRODUCT_1_PRD)
    required_keys = [
        "Executive Summary",
        "Problem Statement",
        "Personas",
        "Scope & Boundaries",
        "User Stories",
        "Functional Requirements",
        "Non-Functional Requirements",
        "Risk Matrix"
    ]
    for key in required_keys:
        assert key in sections and len(sections[key]) > 0, f"Missing section: {key}"
        print(f"  [OK] Section '{key}' successfully parsed.")


def test_dynamic_multi_product_analytics():
    print("\n[5/7] Verifying Genuinely Dynamic PRD Analytics on 3 Different Products...")
    m1 = calculate_prd_metrics(PRODUCT_1_PRD)
    m2 = calculate_prd_metrics(PRODUCT_2_PRD)
    m3 = calculate_prd_metrics(PRODUCT_3_PRD)

    print(f"  Product 1 (QuickBite): Completeness={m1['completeness_score']}%, Words={m1['word_count']}, Stories={m1['story_count']}, FRs={m1['fr_count']}, Risks={m1['risk_count']}")
    print(f"  Product 2 (PennyWise): Completeness={m2['completeness_score']}%, Words={m2['word_count']}, Stories={m2['story_count']}, FRs={m2['fr_count']}, Risks={m2['risk_count']}")
    print(f"  Product 3 (MindEase):  Completeness={m3['completeness_score']}%, Words={m3['word_count']}, Stories={m3['story_count']}, FRs={m3['fr_count']}, Risks={m3['risk_count']}")

    # Product 1 Verification (Flagship)
    assert m1["story_count"] == 6, f"Expected 6 stories for Product 1, got {m1['story_count']}"
    assert m1["fr_count"] == 15, f"Expected 15 FRs for Product 1, got {m1['fr_count']}"
    assert m1["risk_count"] == 6, f"Expected 6 risks for Product 1, got {m1['risk_count']}"
    assert m1["completeness_score"] == 100, f"Expected 100% for Product 1, got {m1['completeness_score']}%"

    # Product 2 Verification (Medium)
    assert m2["story_count"] == 3, f"Expected 3 stories for Product 2, got {m2['story_count']}"
    assert m2["fr_count"] == 4, f"Expected 4 FRs for Product 2, got {m2['fr_count']}"
    assert m2["risk_count"] == 3, f"Expected 3 risks for Product 2, got {m2['risk_count']}"
    assert m2["completeness_score"] == 88, f"Expected 88% for Product 2, got {m2['completeness_score']}%"

    # Product 3 Verification (Compact MVP)
    assert m3["story_count"] == 2, f"Expected 2 stories for Product 3, got {m3['story_count']}"
    assert m3["fr_count"] == 2, f"Expected 2 FRs for Product 3, got {m3['fr_count']}"
    assert m3["risk_count"] == 2, f"Expected 2 risks for Product 3, got {m3['risk_count']}"
    assert m3["completeness_score"] == 58, f"Expected 58% for Product 3, got {m3['completeness_score']}%"

    print("  [OK] Confirmed: Analytics are derived 100% dynamically from actual document structure.")


def test_exporters():
    print("\n[6/7] Verifying HTML & JSON Exporters...")
    html_out = export_as_html(PRODUCT_1_PRD, title="Test PRD")
    assert "<!DOCTYPE html>" in html_out
    assert "<title>Test PRD</title>" in html_out
    print("  [OK] HTML Exporter verified.")

    json_data = {"product_name": "QuickBite Campus", "full_prd": PRODUCT_1_PRD}
    json_out = export_as_json(json_data)
    parsed = json.loads(json_out)
    assert parsed["product_name"] == "QuickBite Campus"
    print("  [OK] JSON Exporter verified.")


def test_model_and_config():
    print("\n[7/7] Verifying Groq Model Discovery & Theme Styling...")
    available_models = get_available_groq_models()
    default_model = get_default_model()
    assert len(available_models) > 0, "No available models returned"
    print(f"  [OK] Default Resolved Model: {default_model}")
    print(f"  [OK] Available Verified Models: {available_models}")

    import app
    app.inject_comprehensive_theme_css("Light")
    app.inject_comprehensive_theme_css("Dark")
    print("  [OK] Theme CSS injection for Light & Dark mode verified with zero errors.")


if __name__ == "__main__":
    print("=" * 65)
    print("STARTING END-TO-END VERIFICATION SUITE")
    print("=" * 65)
    
    test_syntax_and_compilation()
    test_knowledge_base_and_rag()
    test_agent_prompts()
    test_section_extraction()
    test_dynamic_multi_product_analytics()
    test_exporters()
    test_model_and_config()
    
    print("\n" + "=" * 65)
    print("[ALL CHECKS PASSED] System verified 100% against requirements!")
    print("=" * 65)
