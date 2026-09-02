import streamlit as st
import time
from src.config import (
    DEFAULT_GROQ_MODEL,
    get_available_groq_models,
    get_default_model,
    get_groq_api_key,
    CHROMA_PERSIST_DIR
)
from src.rag.vector_store import initialize_vector_store
from src.agents.prd_generator import generate_full_prd
from src.utils.export_utils import (
    sanitize_filename,
    extract_sections,
    calculate_prd_metrics,
    export_as_html,
    export_as_json
)

# Preset ideas for quick testing during college demos
PRESET_IDEAS = {
    "Select a sample idea...": {
        "name": "",
        "domain": "",
        "idea": "",
        "constraints": ""
    },
    "🍔 Campus Food & Coffee Delivery": {
        "name": "QuickBite Campus",
        "domain": "FoodTech / EdTech Logistics",
        "idea": "An on-demand food and coffee delivery app tailored specifically for college campus dorms and lecture halls. It aggregates campus cafeterias and nearby partnered cafes, provides real-time locker or building pin-point delivery, and supports split billing among roommates and campus meal-card integration.",
        "constraints": "Mobile-first responsive app, zero-delivery fee for orders over $10, campus email verification required."
    },
    "💰 Student Smart Budget & Expense Tracker": {
        "name": "PennyWise Student",
        "domain": "FinTech / Personal Finance",
        "idea": "An AI-assisted personal expense and micro-budgeting assistant for college students. It connects to bank accounts, scans receipts using OCR, automatically categorizes expenses, warns students before they run out of allowance, and provides AI-driven saving challenges.",
        "constraints": "Bank-grade encryption, privacy-first (no selling transaction data), offline receipt scanning support."
    },
    "🧠 AI Study Stress & Mental Wellness Companion": {
        "name": "MindEase AI",
        "domain": "Digital Health / Student Well-being",
        "idea": "A supportive conversational AI companion designed to help university students manage exam stress, track emotional burnout, and build balanced study-rest routines with guided micro-meditations and anonymized campus counseling hotlines.",
        "constraints": "Strict crisis escalation protocols, 100% anonymous, not a substitute for clinical psychiatric care."
    },
    "🔄 Campus Skill & Equipment Exchange": {
        "name": "SkillSwap University",
        "domain": "Peer-to-Peer Marketplace",
        "idea": "A localized peer-to-peer marketplace where university students can trade tutoring hours, borrow expensive lab equipment/cameras, and collaborate on student portfolio projects using a campus-verified reputation credit system.",
        "constraints": "Campus SSO verification, deposit escrow for hardware loans, review verification."
    }
}

# Streamlit Page Configuration
st.set_page_config(
    page_title="AI Product Requirement Generator",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)


def inject_comprehensive_theme_css(theme_mode: str):
    """
    Inject a comprehensive, WCAG-compliant design system for Light and Dark modes.
    Overrides all Streamlit default component styling to eliminate contrast issues.
    """
    is_dark = (theme_mode == "Dark")
    
    if is_dark:
        # Dark Theme Palette (Deep Navy / Slate)
        c_bg_main = "#0B0F19"
        c_bg_sidebar = "#111827"
        c_bg_card = "#151E2E"
        c_bg_card_inner = "#1A2538"
        c_bg_input = "#0F172A"
        c_bg_tab_bar = "#111827"
        c_bg_tab_active = "#1E293B"
        c_bg_table_th = "#1E293B"
        c_bg_table_tr_alt = "#111827"
        c_bg_code = "#0F172A"
        
        c_border = "#243247"
        c_border_focus = "#3B82F6"
        c_border_table = "#243247"
        
        c_text_primary = "#F8FAFC"       # Crisp white/slate
        c_text_secondary = "#CBD5E1"     # Highly readable light gray
        c_text_muted = "#94A3B8"         # Clear muted gray
        c_text_placeholder = "#64748B"
        c_text_accent = "#60A5FA"        # Bright blue
        
        c_badge_bg = "rgba(37, 99, 235, 0.2)"
        c_badge_border = "#2563EB"
        c_badge_text = "#93C5FD"
        
        c_step_active_bg = "#2563EB"
        c_step_active_text = "#FFFFFF"
        c_step_inactive_bg = "#1A2538"
        c_step_inactive_border = "#243247"
        c_step_inactive_text = "#94A3B8"
        
        c_metric_val = "#38BDF8"
        c_metric_bg = "#151E2E"
        
        c_btn_sec_bg = "#1E293B"
        c_btn_sec_border = "#334155"
        c_btn_sec_text = "#F8FAFC"
        c_btn_sec_hover = "#273549"
        
        header_title_color = "linear-gradient(135deg, #93C5FD 0%, #60A5FA 50%, #A78BFA 100%)"
        box_shadow_card = "0 4px 20px rgba(0, 0, 0, 0.4)"
        box_shadow_btn = "0 4px 14px rgba(37, 99, 235, 0.35)"
    else:
        # Light Theme Palette (Clean Slate / SaaS White)
        c_bg_main = "#F8FAFC"
        c_bg_sidebar = "#FFFFFF"
        c_bg_card = "#FFFFFF"
        c_bg_card_inner = "#F8FAFC"
        c_bg_input = "#FFFFFF"
        c_bg_tab_bar = "#F1F5F9"
        c_bg_tab_active = "#FFFFFF"
        c_bg_table_th = "#F1F5F9"
        c_bg_table_tr_alt = "#F8FAFC"
        c_bg_code = "#F1F5F9"
        
        c_border = "#E2E8F0"
        c_border_focus = "#2563EB"
        c_border_table = "#E2E8F0"
        
        c_text_primary = "#0F172A"       # Deep slate black
        c_text_secondary = "#334155"     # Clear readable dark slate
        c_text_muted = "#475569"         # Slate gray
        c_text_placeholder = "#94A3B8"
        c_text_accent = "#1D4ED8"        # Deep blue
        
        c_badge_bg = "#EFF6FF"
        c_badge_border = "#BFDBFE"
        c_badge_text = "#1D4ED8"
        
        c_step_active_bg = "#2563EB"
        c_step_active_text = "#FFFFFF"
        c_step_inactive_bg = "#F8FAFC"
        c_step_inactive_border = "#E2E8F0"
        c_step_inactive_text = "#475569"
        
        c_metric_val = "#1D4ED8"
        c_metric_bg = "#FFFFFF"
        
        c_btn_sec_bg = "#F8FAFC"
        c_btn_sec_border = "#CBD5E1"
        c_btn_sec_text = "#0F172A"
        c_btn_sec_hover = "#F1F5F9"
        
        header_title_color = "linear-gradient(135deg, #1E3A8A 0%, #2563EB 100%)"
        box_shadow_card = "0 2px 10px rgba(15, 23, 42, 0.05)"
        box_shadow_btn = "0 4px 14px rgba(37, 99, 235, 0.25)"

    st.markdown(f"""
    <style>
        /* ==========================================================
           0. HIDE DEFAULT STREAMLIT CHROME (Deploy button, MainMenu, Footer)
           ========================================================== */
        #MainMenu,
        div[data-testid="stMainMenu"],
        .stDeployButton,
        div[data-testid="stDeployButton"],
        div[data-testid="stToolbarActions"],
        div[data-testid="stDecoration"],
        div[data-testid="stStatusWidget"],
        div[data-testid="stHeaderActionElements"],
        div[data-testid="stToolbar"],
        footer,
        div[data-testid="stFooter"] {{
            display: none !important;
            visibility: hidden !important;
        }}

        header[data-testid="stHeader"] {{
            background-color: transparent !important;
        }}

        /* Keyframes for loading icon spin */
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}

        .spinning-loader {{
            display: inline-block;
            font-size: 2.4rem;
            animation: spin 2.5s linear infinite;
        }}

        /* ==========================================================
           1. CORE APPLICATION BACKGROUND & BASE TYPOGRAPHY
           ========================================================== */
        .stApp, div[data-testid="stAppViewContainer"], div[data-testid="stAppViewBlockContainer"] {{
            background-color: {c_bg_main} !important;
            color: {c_text_primary} !important;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif !important;
        }}

        /* Universal Text Contrast */
        h1, h2, h3, h4, h5, h6, p, li, span, label, div {{
            color: {c_text_primary};
        }}

        /* Sidebar Styling */
        section[data-testid="stSidebar"], div[data-testid="stSidebarContent"] {{
            background-color: {c_bg_sidebar} !important;
            border-right: 1px solid {c_border} !important;
            color: {c_text_primary} !important;
        }}
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span {{
            color: {c_text_primary} !important;
        }}

        /* ==========================================================
           2. HERO HEADER & WORKFLOW STEPPER
           ========================================================== */
        .hero-container {{
            background: {c_bg_card};
            border: 1px solid {c_border};
            border-radius: 14px;
            padding: 1.8rem 2rem;
            margin-bottom: 1.5rem;
            box-shadow: {box_shadow_card};
        }}
        .hero-badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 700;
            background-color: {c_badge_bg};
            border: 1px solid {c_badge_border};
            color: {c_badge_text};
            margin-bottom: 0.8rem;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }}
        .hero-title {{
            font-size: 2.2rem;
            font-weight: 800;
            line-height: 1.25;
            background: {header_title_color};
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.4rem;
        }}
        .hero-desc {{
            font-size: 1.02rem;
            color: {c_text_secondary} !important;
            line-height: 1.55;
            max-width: 860px;
            margin-bottom: 1.2rem;
        }}

        /* Workflow Stepper Indicator */
        .stepper-bar {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            align-items: center;
            padding-top: 0.8rem;
            border-top: 1px solid {c_border};
        }}
        .step-pill {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 14px;
            border-radius: 8px;
            font-size: 0.82rem;
            font-weight: 600;
            background: {c_step_inactive_bg};
            border: 1px solid {c_step_inactive_border};
            color: {c_step_inactive_text};
        }}
        .step-pill.active {{
            background: {c_step_active_bg};
            border-color: {c_step_active_bg};
            color: {c_step_active_text};
        }}
        .step-divider {{
            color: {c_text_muted};
            font-size: 0.85rem;
        }}

        /* ==========================================================
           3. CARD CONTAINERS & SECTION BOXES
           ========================================================== */
        .saas-card {{
            background-color: {c_bg_card};
            border: 1px solid {c_border};
            border-radius: 12px;
            padding: 1.5rem 1.8rem;
            margin-bottom: 1.5rem;
            box-shadow: {box_shadow_card};
        }}
        .saas-card-title {{
            font-size: 1.18rem;
            font-weight: 700;
            color: {c_text_primary} !important;
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 0.3rem;
        }}
        .saas-card-desc {{
            font-size: 0.88rem;
            color: {c_text_secondary} !important;
            margin-bottom: 1.2rem;
            line-height: 1.4;
        }}

        /* ==========================================================
           4. FORM INPUTS, LABELS, SELECTORS & DROPDOWNS
           ========================================================== */
        /* Widget Labels */
        div[data-testid="stWidgetLabel"] label,
        div[data-testid="stWidgetLabel"] p,
        div[data-testid="stWidgetLabel"] span {{
            color: {c_text_primary} !important;
            font-weight: 600 !important;
            font-size: 0.92rem !important;
            margin-bottom: 4px !important;
        }}

        /* Inputs & Textareas */
        .stTextInput input,
        .stTextArea textarea,
        div[data-baseweb="base-input"] input,
        div[data-baseweb="textarea"] textarea {{
            background-color: {c_bg_input} !important;
            color: {c_text_primary} !important;
            border: 1px solid {c_border} !important;
            border-radius: 8px !important;
            font-size: 0.95rem !important;
            padding: 0.65rem 0.85rem !important;
        }}
        .stTextInput input:focus,
        .stTextArea textarea:focus,
        div[data-baseweb="base-input"] input:focus,
        div[data-baseweb="textarea"] textarea:focus {{
            border-color: {c_border_focus} !important;
            box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.25) !important;
            outline: none !important;
        }}
        .stTextInput input::placeholder,
        .stTextArea textarea::placeholder,
        div[data-baseweb="base-input"] input::placeholder,
        div[data-baseweb="textarea"] textarea::placeholder {{
            color: {c_text_placeholder} !important;
            opacity: 1 !important;
        }}

        /* Selectboxes - Main Trigger Control */
        div[data-testid="stSelectbox"] > div,
        div[data-baseweb="select"],
        div[data-baseweb="select"] > div {{
            background-color: {c_bg_input} !important;
            background: {c_bg_input} !important;
            border: 1px solid {c_border} !important;
            border-radius: 8px !important;
            color: {c_text_primary} !important;
        }}
        div[data-baseweb="select"]:hover,
        div[data-baseweb="select"] > div:hover {{
            border-color: {c_border_focus} !important;
        }}
        div[data-baseweb="select"] span,
        div[data-baseweb="select"] div,
        div[data-baseweb="select"] p {{
            color: {c_text_primary} !important;
        }}
        div[data-baseweb="select"] svg {{
            fill: {c_text_muted} !important;
            color: {c_text_muted} !important;
        }}

        /* Selectboxes - Dropdown Popover & Listbox Container */
        div[data-baseweb="popover"],
        div[data-baseweb="popover"] > div,
        div[data-baseweb="menu"],
        ul[role="listbox"],
        div[role="listbox"] {{
            background-color: {c_bg_card} !important;
            background: {c_bg_card} !important;
            border: 1px solid {c_border} !important;
            border-radius: 8px !important;
            color: {c_text_primary} !important;
            padding: 4px !important;
            box-shadow: {box_shadow_card} !important;
        }}

        /* Selectbox Option Items */
        li[role="option"],
        li[data-baseweb="menu-item"],
        div[role="option"] {{
            background-color: {c_bg_card} !important;
            background: {c_bg_card} !important;
            color: {c_text_primary} !important;
            border-radius: 6px !important;
            padding: 8px 12px !important;
            font-size: 0.9rem !important;
            cursor: pointer !important;
            transition: all 0.15s ease !important;
        }}
        li[role="option"] span,
        li[role="option"] div,
        li[role="option"] p,
        li[data-baseweb="menu-item"] span,
        li[data-baseweb="menu-item"] div {{
            color: {c_text_primary} !important;
        }}
        li[role="option"]:hover,
        li[data-baseweb="menu-item"]:hover {{
            background-color: {c_bg_card_inner} !important;
            background: {c_bg_card_inner} !important;
            color: {c_text_accent} !important;
        }}
        li[role="option"]:hover span,
        li[role="option"]:hover div,
        li[data-baseweb="menu-item"]:hover span,
        li[data-baseweb="menu-item"]:hover div {{
            color: {c_text_accent} !important;
        }}
        li[role="option"][aria-selected="true"],
        li[data-baseweb="menu-item"][aria-selected="true"] {{
            background-color: {c_step_active_bg} !important;
            background: {c_step_active_bg} !important;
            color: #FFFFFF !important;
            font-weight: 700 !important;
        }}
        li[role="option"][aria-selected="true"] span,
        li[role="option"][aria-selected="true"] div,
        li[data-baseweb="menu-item"][aria-selected="true"] span,
        li[data-baseweb="menu-item"][aria-selected="true"] div {{
            color: #FFFFFF !important;
        }}

        /* Radio Buttons */
        div[data-testid="stRadio"] label,
        div[data-testid="stRadio"] span,
        div[data-testid="stRadio"] p {{
            color: {c_text_primary} !important;
            font-weight: 600 !important;
        }}

        /* Expanders */
        div[data-testid="stExpander"] {{
            background-color: {c_bg_card_inner} !important;
            border: 1px solid {c_border} !important;
            border-radius: 10px !important;
        }}
        div[data-testid="stExpander"] details {{
            background-color: transparent !important;
        }}
        div[data-testid="stExpander"] summary span {{
            color: {c_text_primary} !important;
            font-weight: 600 !important;
        }}

        /* ==========================================================
           5. BUTTONS (PRIMARY & SECONDARY EXPORT BUTTONS)
           ========================================================== */
        /* Primary Action Button */
        div.stButton > button[kind="primary"] {{
            background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 10px !important;
            padding: 0.75rem 1.6rem !important;
            font-size: 1.05rem !important;
            font-weight: 700 !important;
            box-shadow: {box_shadow_btn} !important;
            width: 100% !important;
            cursor: pointer !important;
            transition: all 0.2s ease !important;
        }}
        div.stButton > button[kind="primary"]:hover {{
            background: linear-gradient(135deg, #1D4ED8 0%, #1E40AF 100%) !important;
            box-shadow: 0 6px 20px rgba(37, 99, 235, 0.45) !important;
            transform: translateY(-1px) !important;
        }}

        /* Standard Secondary Buttons */
        div.stButton > button:not([kind="primary"]) {{
            background-color: {c_btn_sec_bg} !important;
            color: {c_btn_sec_text} !important;
            border: 1px solid {c_btn_sec_border} !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            padding: 0.5rem 1rem !important;
            transition: all 0.2s ease !important;
        }}
        div.stButton > button:not([kind="primary"]):hover {{
            background-color: {c_btn_sec_hover} !important;
            border-color: {c_border_focus} !important;
        }}

        /* Download Buttons */
        div.stDownloadButton > button {{
            background-color: {c_btn_sec_bg} !important;
            color: {c_btn_sec_text} !important;
            border: 1px solid {c_btn_sec_border} !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            font-size: 0.88rem !important;
            padding: 0.55rem 1rem !important;
            width: 100% !important;
            transition: all 0.2s ease !important;
        }}
        div.stDownloadButton > button:hover {{
            background-color: {c_btn_sec_hover} !important;
            border-color: {c_border_focus} !important;
            color: {c_text_accent} !important;
        }}

        /* ==========================================================
           6. METRIC TILES & ANALYTICS BAR
           ========================================================== */
        .metric-box {{
            background-color: {c_metric_bg};
            border: 1px solid {c_border};
            border-radius: 10px;
            padding: 1.1rem 0.8rem;
            text-align: center;
            box-shadow: {box_shadow_card};
            transition: transform 0.15s ease;
        }}
        .metric-box:hover {{
            transform: translateY(-2px);
        }}
        .metric-box-val {{
            font-size: 1.75rem;
            font-weight: 800;
            color: {c_metric_val};
            margin-bottom: 0.2rem;
            line-height: 1.2;
        }}
        .metric-box-lbl {{
            font-size: 0.78rem;
            color: {c_text_muted} !important;
            text-transform: uppercase;
            font-weight: 700;
            letter-spacing: 0.05em;
        }}

        /* ==========================================================
           7. TABS, TABLES & MARKDOWN RENDERING
           ========================================================== */
        /* Tab Bar Navigation */
        .stTabs [data-baseweb="tab-list"] {{
            background-color: {c_bg_tab_bar} !important;
            border: 1px solid {c_border} !important;
            border-radius: 10px !important;
            padding: 6px !important;
            gap: 6px !important;
        }}
        .stTabs [data-baseweb="tab"] {{
            background-color: transparent !important;
            border-radius: 8px !important;
            padding: 8px 16px !important;
            font-weight: 600 !important;
            font-size: 0.9rem !important;
            color: {c_text_muted} !important;
            border: none !important;
        }}
        .stTabs [aria-selected="true"] {{
            background-color: {c_bg_tab_active} !important;
            color: {c_text_accent} !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
        }}
        .stTabs [data-baseweb="tab-border"] {{
            display: none !important;
        }}

        /* Tab Content Panel Card */
        div[data-baseweb="tab-panel"] {{
            background-color: {c_bg_card} !important;
            border: 1px solid {c_border} !important;
            border-radius: 12px !important;
            padding: 1.8rem 2rem !important;
            margin-top: 1rem !important;
            box-shadow: {box_shadow_card} !important;
        }}
        div[data-baseweb="tab-panel"] h1,
        div[data-baseweb="tab-panel"] h2,
        div[data-baseweb="tab-panel"] h3 {{
            color: {c_text_primary} !important;
            margin-top: 1rem !important;
            margin-bottom: 0.6rem !important;
        }}
        div[data-baseweb="tab-panel"] p,
        div[data-baseweb="tab-panel"] li {{
            color: {c_text_secondary} !important;
            font-size: 0.98rem !important;
            line-height: 1.65 !important;
        }}
        div[data-baseweb="tab-panel"] strong {{
            color: {c_text_primary} !important;
            font-weight: 700 !important;
        }}

        /* Markdown Tables (Functional specs, NFRs, Risk matrix) */
        table {{
            width: 100% !important;
            border-collapse: collapse !important;
            margin: 1.2rem 0 !important;
            background-color: {c_bg_card} !important;
            border: 1px solid {c_border_table} !important;
            border-radius: 8px !important;
            overflow: hidden !important;
        }}
        th {{
            background-color: {c_bg_table_th} !important;
            color: {c_text_primary} !important;
            font-weight: 700 !important;
            text-align: left !important;
            padding: 10px 14px !important;
            border-bottom: 2px solid {c_border_table} !important;
            border-right: 1px solid {c_border_table} !important;
            font-size: 0.9rem !important;
        }}
        td {{
            padding: 10px 14px !important;
            color: {c_text_secondary} !important;
            border-bottom: 1px solid {c_border_table} !important;
            border-right: 1px solid {c_border_table} !important;
            font-size: 0.9rem !important;
            line-height: 1.4 !important;
        }}
        tr:nth-child(even) td {{
            background-color: {c_bg_table_tr_alt} !important;
        }}

        /* Code Blocks & RAG Output */
        code, pre {{
            background-color: {c_bg_code} !important;
            color: {c_text_primary} !important;
            border: 1px solid {c_border} !important;
            border-radius: 6px !important;
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace !important;
        }}
        
        /* Status Card */
        .status-badge-chip {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 0.82rem;
            font-weight: 600;
            background-color: {c_bg_card_inner};
            border: 1px solid {c_border};
            color: {c_text_accent};
        }}
    </style>
    """, unsafe_allow_html=True)


def render_input_page(env_key, selected_model, selected_preset):
    """Render the Product Definition & Pipeline Launch View."""
    st.markdown("""
    <div class="hero-container">
        <div class="hero-badge">⚡ Dual-Agent AI Pipeline (BA + PM) &bull; RAG Vector Grounding</div>
        <div class="hero-title">AI Product Requirement Generator</div>
        <div class="hero-desc">
            Transform high-level product ideas into comprehensive, execution-ready Product Requirement Documents (PRDs).
            Powered by specialized Business Analyst and Product Manager AI agents running on Groq with ChromaDB knowledge retrieval.
        </div>
        <div class="stepper-bar">
            <span class="step-pill active">① Define Product Concept</span>
            <span class="step-divider">➔</span>
            <span class="step-pill">② Dual-Agent Generation</span>
            <span class="step-divider">➔</span>
            <span class="step-pill">③ Dedicated PRD Results Page</span>
            <span class="step-divider">➔</span>
            <span class="step-pill">④ Multi-Format Export</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # If a PRD is already in session, display quick navigation banner
    if "last_prd" in st.session_state and st.session_state["last_prd"]:
        prd_obj = st.session_state["last_prd"]
        p_name = prd_obj.get("product_name", "Generated Product")
        p_metrics = calculate_prd_metrics(prd_obj.get("full_prd", ""))
        
        col_banner, col_btn = st.columns([3, 1])
        with col_banner:
            st.info(f"📄 **Active PRD in Session**: **{p_name}** ({p_metrics['story_count']} Stories • {p_metrics['fr_count']} FRs • {p_metrics['risk_count']} Risks • {p_metrics['word_count']} Words)")
        with col_btn:
            if st.button("📄 View Generated PRD", use_container_width=True):
                st.session_state["current_view"] = "results"
                st.rerun()

    # Populate preset data if selected
    preset_data = PRESET_IDEAS.get(selected_preset, {})
    default_name = preset_data.get("name", "")
    default_domain = preset_data.get("domain", "")
    default_idea = preset_data.get("idea", "")
    default_constraints = preset_data.get("constraints", "")

    # Input Form Card
    with st.container():
        st.markdown("""
        <div class="saas-card">
            <div class="saas-card-title">📝 Step 1: Define Product Concept & Parameters</div>
            <div class="saas-card-desc">Enter your product vision. The Business Analyst Agent evaluates market viability and user personas, while the Product Manager Agent structures technical specifications, INVEST user stories, and risk matrices.</div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns([2, 1])
        with col1:
            product_name = st.text_input(
                "Product Name *",
                value=default_name,
                placeholder="e.g., QuickBite Campus, SkillSwap University, PennyWise"
            )
        with col2:
            domain = st.text_input(
                "Industry / Domain *",
                value=default_domain,
                placeholder="e.g., EdTech, FinTech, FoodTech, HealthTech"
            )

        product_idea = st.text_area(
            "Product Concept & Pitch (What problem does it solve? Who is it for?) *",
            value=default_idea,
            height=125,
            placeholder="Describe what your product does, the core problem it solves, target users, and unique value proposition..."
        )

        with st.expander("🛠️ Technical & Business Constraints (Optional)", expanded=False):
            constraints = st.text_input(
                "Scope Boundaries, Platform Constraints, SLAs",
                value=default_constraints,
                placeholder="e.g., Mobile-first responsive app, offline mode, GDPR compliance, sub-200ms latency"
            )

        generate_btn = st.button("🚀 Generate Structured PRD", type="primary", use_container_width=True)

    # Execution Trigger Handling: Immediately transition to dedicated Results page for live loading state
    if generate_btn:
        if not env_key:
            st.error("⚠️ Groq API Key not detected. Please configure `GROQ_API_KEY` in your local `.env` file in the project root to generate PRDs.")
            return

        if not product_name.strip() or not product_idea.strip():
            st.error("⚠️ Please provide both a Product Name and a Product Concept description.")
            return

        # Set generation parameters and route immediately to the dedicated PRD Results page
        st.session_state["generating"] = True
        st.session_state["gen_params"] = {
            "product_name": product_name.strip(),
            "product_idea": product_idea.strip(),
            "domain": domain.strip() if domain.strip() else "General Tech",
            "constraints": constraints.strip() if constraints.strip() else "Standard web/mobile platform",
            "model_name": selected_model,
            "groq_api_key": env_key
        }
        st.session_state["gen_error"] = None
        st.session_state["current_view"] = "results"
        st.rerun()


def render_results_page():
    """Render the Dedicated PRD Results Page containing only PRD-related information."""
    
    # -------------------------------------------------------------
    # Case A: An error occurred during generation
    # -------------------------------------------------------------
    if st.session_state.get("gen_error"):
        st.markdown(f"""
        <div class="saas-card" style="border-left: 4px solid #EF4444; padding: 2rem;">
            <div class="saas-card-title" style="color: #EF4444 !important; font-size: 1.3rem;">❌ PRD Generation Failed</div>
            <div class="saas-card-desc" style="font-size: 1rem; margin-top: 0.5rem; margin-bottom: 1.2rem; color: #DC2626 !important;">
                {st.session_state['gen_error']}
            </div>
            <p style="font-size: 0.9rem; color: #6B7280;">Tip: Verify your Groq API key, model selection, or rate limits at https://console.groq.com</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("⬅️ Return to Product Input", type="primary"):
            st.session_state["gen_error"] = None
            st.session_state["generating"] = False
            st.session_state["current_view"] = "input"
            st.rerun()
        return

    # -------------------------------------------------------------
    # Case B: Active PRD Generation in Progress (Loading State on Results Page)
    # -------------------------------------------------------------
    if st.session_state.get("generating") and st.session_state.get("gen_params"):
        params = st.session_state["gen_params"]
        
        # Navigation / Cancel Option
        col_nav, _ = st.columns([1, 4])
        with col_nav:
            if st.button("⬅️ Cancel & Back to Input", use_container_width=True):
                st.session_state["generating"] = False
                st.session_state["gen_params"] = None
                st.session_state["current_view"] = "input"
                st.rerun()

        # Dedicated Loading Hero Header
        st.markdown(f"""
        <div class="hero-container" style="margin-top: 0.5rem;">
            <div class="hero-badge">⚡ AI Pipeline In Progress &bull; {params['model_name']}</div>
            <div class="hero-title">📋 Generating PRD: {params['product_name']}</div>
            <div class="hero-desc">
                <strong>Domain / Industry</strong>: {params['domain']} &nbsp;|&nbsp; 
                <strong>Status</strong>: Multi-Agent Synthesis in Progress
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Clear Loading State Card
        st.markdown("""
        <div class="saas-card" style="text-align: center; padding: 2.5rem 2rem;">
            <div class="spinning-loader">⚙️</div>
            <div class="saas-card-title" style="justify-content: center; font-size: 1.35rem; margin-top: 0.8rem;">
                Generating your structured PRD...
            </div>
            <div class="saas-card-desc" style="font-size: 1.02rem; margin-top: 0.4rem; margin-bottom: 1.2rem;">
                Running AI analysis and RAG knowledge retrieval... Please wait...
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Progress bar and live status updates
        progress_bar = st.progress(0.05)
        status_text = st.empty()
        status_text.markdown("**Initializing dual-agent pipeline and querying ChromaDB vector store...**")

        def update_progress(message: str, value: float):
            progress_bar.progress(value)
            status_text.markdown(f"**{message}**")

        try:
            start_time = time.time()
            prd_result = generate_full_prd(
                product_name=params["product_name"],
                product_idea=params["product_idea"],
                domain=params["domain"],
                constraints=params["constraints"],
                groq_api_key=params["groq_api_key"],
                model_name=params["model_name"],
                progress_callback=update_progress
            )
            elapsed_time = round(time.time() - start_time, 2)
            progress_bar.progress(1.0)
            status_text.success(f"🎉 Product Requirement Document generated in {elapsed_time}s!")
            time.sleep(0.4)

            # Store in session state & automatically replace loading state with generated PRD results
            st.session_state["last_prd"] = prd_result
            st.session_state["last_prd_time"] = elapsed_time
            st.session_state["history"].append(prd_result)
            st.session_state["generating"] = False
            st.session_state["gen_params"] = None
            st.rerun()

        except Exception as e:
            st.session_state["generating"] = False
            st.session_state["gen_params"] = None
            st.session_state["gen_error"] = str(e)
            st.rerun()
        return

    # -------------------------------------------------------------
    # Case C: Empty State (No PRD generated yet)
    # -------------------------------------------------------------
    if "last_prd" not in st.session_state or not st.session_state["last_prd"]:
        st.markdown("""
        <div class="saas-card" style="text-align: center; padding: 3rem 2rem;">
            <div style="font-size: 2.5rem; margin-bottom: 1rem;">📄</div>
            <div class="saas-card-title" style="justify-content: center;">No PRD Generated Yet</div>
            <div class="saas-card-desc">Please define your product idea and launch the AI generation pipeline to generate a structured PRD.</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("⬅️ Go to Product Input", type="primary"):
            st.session_state["current_view"] = "input"
            st.rerun()
        return

    # -------------------------------------------------------------
    # Case D: Generated PRD Available (Results Display)
    # -------------------------------------------------------------
    prd_data = st.session_state["last_prd"]
    full_prd = prd_data["full_prd"]
    clean_base = sanitize_filename(prd_data['product_name'])
    sections = extract_sections(full_prd)
    metrics = calculate_prd_metrics(full_prd)
    model_display = prd_data.get("model_used") or DEFAULT_GROQ_MODEL

    # Top Header & Navigation Bar
    col_nav, col_hero = st.columns([1, 4])
    with col_nav:
        if st.button("⬅️ Back to Input", use_container_width=True):
            st.session_state["current_view"] = "input"
            st.rerun()

    st.markdown(f"""
    <div class="hero-container" style="margin-top: 0.5rem;">
        <div class="hero-badge">✨ Generated PRD Specification &bull; {model_display}</div>
        <div class="hero-title">📋 {prd_data['product_name']}</div>
        <div class="hero-desc">
            <strong>Domain / Industry</strong>: {prd_data.get('domain', 'General Tech')} &nbsp;|&nbsp; 
            <strong>Status</strong>: Ready &bull; Verified &nbsp;|&nbsp; 
            <strong>Generated via</strong>: Dual-Agent Pipeline (BA + PM) + ChromaDB RAG
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 1. PRD Analytics & Metrics Dashboard (5 Core Metrics - Completeness Removed)
    st.markdown("### 📊 PRD Quality & Scope Analytics")
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-box-val">{metrics['word_count']}</div>
            <div class="metric-box-lbl">Total Words</div>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-box-val">{metrics['persona_count']}</div>
            <div class="metric-box-lbl">Personas</div>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-box-val">{metrics['story_count']}</div>
            <div class="metric-box-lbl">User Stories</div>
        </div>
        """, unsafe_allow_html=True)
    with m4:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-box-val">{metrics['fr_count']}</div>
            <div class="metric-box-lbl">Functional Reqs</div>
        </div>
        """, unsafe_allow_html=True)
    with m5:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-box-val">{metrics['risk_count']}</div>
            <div class="metric-box-lbl">Risk Items</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    # 2. Multi-Format Export Toolbar
    st.markdown("### 📥 Document Exports & Actions")
    exp1, exp2, exp3, exp4 = st.columns([1.2, 1.2, 1.2, 2.4])
    with exp1:
        st.download_button(
            label="📥 Download Markdown (.md)",
            data=full_prd,
            file_name=f"PRD_{clean_base}.md",
            mime="text/markdown",
            use_container_width=True
        )
    with exp2:
        html_content = export_as_html(full_prd, title=f"PRD - {prd_data['product_name']}")
        st.download_button(
            label="📄 Printable HTML (.html)",
            data=html_content,
            file_name=f"PRD_{clean_base}.html",
            mime="text/html",
            use_container_width=True
        )
    with exp3:
        json_content = export_as_json(prd_data)
        st.download_button(
            label="📦 Export JSON (.json)",
            data=json_content,
            file_name=f"PRD_{clean_base}.json",
            mime="application/json",
            use_container_width=True
        )
    with exp4:
        st.caption(f"**Verified Model**: `{model_display}` &bull; **Estimated Read Time**: `~{metrics['read_time_min']} min`")

    st.markdown("<br/>", unsafe_allow_html=True)

    # 3. Dedicated PRD Sections & Deep Document Workspace
    st.markdown("### 📋 Structured Requirements Document")
    tabs = st.tabs([
        "📋 Full PRD Document",
        "💡 Executive Summary & Scope",
        "👥 User Personas (BA)",
        "📝 User Stories & Acceptance Criteria",
        "⚙️ Functional Requirements",
        "⚡ Non-Functional Requirements & SLAs",
        "⚠️ Risk Assessment & Mitigations",
        "🔍 RAG Knowledge Trace"
    ])

    with tabs[0]:
        st.markdown(full_prd)

    with tabs[1]:
        st.markdown("### 💡 Executive Summary, Problem Definition & Scope Boundaries")
        if sections.get("Executive Summary") or sections.get("Problem Statement"):
            if sections.get("Executive Summary"):
                st.markdown(sections["Executive Summary"])
            if sections.get("Problem Statement"):
                st.markdown(sections["Problem Statement"])
            if sections.get("Scope & Boundaries"):
                st.markdown(sections["Scope & Boundaries"])
        else:
            st.markdown(prd_data["ba_output"])

    with tabs[2]:
        st.markdown("### 👥 Target User Personas & Demographics")
        if sections.get("Personas"):
            st.markdown(sections["Personas"])
        else:
            st.markdown(prd_data["ba_output"])

    with tabs[3]:
        st.markdown("### 📝 User Stories & Gherkin Acceptance Criteria")
        if sections.get("User Stories"):
            st.markdown(sections["User Stories"])
        else:
            st.markdown(prd_data["pm_output"])

    with tabs[4]:
        st.markdown("### ⚙️ Functional Requirements (MoSCoW Prioritization)")
        if sections.get("Functional Requirements"):
            st.markdown(sections["Functional Requirements"])
        else:
            st.info("Functional Requirements are available in the Full PRD tab.")

    with tabs[5]:
        st.markdown("### ⚡ Non-Functional Requirements, SLAs & Quality Attributes")
        if sections.get("Non-Functional Requirements"):
            st.markdown(sections["Non-Functional Requirements"])
        else:
            st.info("Non-Functional Requirements are available in the Full PRD tab.")

    with tabs[6]:
        st.markdown("### ⚠️ Risk Assessment Matrix & Mitigation Strategies")
        if sections.get("Risk Matrix"):
            st.markdown(sections["Risk Matrix"])
        else:
            st.info("Risk Assessment is available in the Full PRD tab.")

    with tabs[7]:
        st.markdown("### 🔍 RAG Knowledge Base Retrieval Trace")
        st.markdown("**1. Business Analyst Stage Retrieved Guidelines:**")
        st.code(prd_data.get("ba_rag_context", "None"), language="markdown")
        st.markdown("**2. Product Manager Stage Retrieved Standards:**")
        st.code(prd_data.get("pm_rag_context", "None"), language="markdown")

    st.markdown("---")
    if st.button("⬅️ Create Another PRD / Back to Input", use_container_width=True):
        st.session_state["current_view"] = "input"
        st.rerun()


def main():
    # Session state initialization
    if "history" not in st.session_state:
        st.session_state["history"] = []
    if "theme_mode" not in st.session_state:
        st.session_state["theme_mode"] = "Light"
    if "current_view" not in st.session_state:
        st.session_state["current_view"] = "input"
    if "generating" not in st.session_state:
        st.session_state["generating"] = False
    if "gen_params" not in st.session_state:
        st.session_state["gen_params"] = None
    if "gen_error" not in st.session_state:
        st.session_state["gen_error"] = None

    # Sidebar Controls
    with st.sidebar:
        st.markdown("### ⚙️ Workspace Control")
        
        # 1. Theme Toggle
        theme_choice = st.radio(
            "Visual Theme",
            options=["☀️ Light", "🌙 Dark"],
            index=0 if st.session_state["theme_mode"] == "Light" else 1,
            horizontal=True,
            label_visibility="collapsed"
        )
        st.session_state["theme_mode"] = "Light" if "Light" in theme_choice else "Dark"

        # Apply comprehensive styling dynamically
        inject_comprehensive_theme_css(st.session_state["theme_mode"])

        st.markdown("---")
        st.subheader("🧭 Navigation View")
        
        # Page View Selector
        is_generating = st.session_state.get("generating", False)
        has_prd = bool("last_prd" in st.session_state and st.session_state["last_prd"])
        status_suffix = " ⏳" if is_generating else (" ✓" if has_prd else "")
        view_options = ["🏠 Product Input", f"📄 PRD Results{status_suffix}"]
        curr_idx = 0 if st.session_state["current_view"] == "input" else 1
        
        selected_view = st.radio(
            "Active View",
            options=view_options,
            index=curr_idx,
            label_visibility="collapsed"
        )
        st.session_state["current_view"] = "input" if "Product Input" in selected_view else "results"

        st.markdown("---")
        st.subheader("🔑 LLM Configuration")
        
        # Secure API Key loading from .env
        env_key = get_groq_api_key()
        available_models = get_available_groq_models(env_key)
        default_model = get_default_model(env_key)

        if env_key:
            st.markdown('<span class="status-badge-chip">🔒 API Key Connected (.env)</span>', unsafe_allow_html=True)
        else:
            st.warning(
                "**Groq API Key Required**\n\n"
                "Add your API key to the local `.env` file in the project root:\n\n"
                "`GROQ_API_KEY=gsk_...`\n\n"
                "*Get a free key from [console.groq.com](https://console.groq.com).* ",
                icon="⚠️"
            )

        # Model Selector with dynamically verified models
        default_idx = available_models.index(default_model) if default_model in available_models else 0
        selected_model = st.selectbox(
            "Groq LLM Model",
            options=available_models,
            index=default_idx,
            help="Active models verified for your Groq environment."
        )

        st.markdown("---")
        st.subheader("📚 Knowledge Base (RAG)")
        vector_status = "Ready & Indexed" if CHROMA_PERSIST_DIR.exists() else "Ready to build"
        st.caption(f"**ChromaDB Vector Store**: `{vector_status}`")
        st.caption("Embeddings: `sentence-transformers/all-MiniLM-L6-v2`")
        
        if st.button("🔄 Rebuild Vector Index", use_container_width=True):
            with st.spinner("Re-indexing PRD domain documents into ChromaDB..."):
                initialize_vector_store(force_reload=True)
                st.success("Knowledge Base successfully re-indexed!")

        st.markdown("---")
        st.subheader("💡 Demo Quick-Start Presets")
        selected_preset = st.selectbox(
            "Load Example Product Idea:",
            options=list(PRESET_IDEAS.keys())
        )

        if st.session_state["history"]:
            st.markdown("---")
            st.subheader("📜 Session History")
            hist_options = [f"{i+1}. {item['product_name']}" for i, item in enumerate(st.session_state["history"])]
            selected_hist = st.selectbox("Switch to past PRD:", options=["Current Active"] + hist_options)
            if selected_hist != "Current Active":
                idx = int(selected_hist.split(".")[0]) - 1
                st.session_state["last_prd"] = st.session_state["history"][idx]
                st.session_state["current_view"] = "results"

        st.markdown("---")
        with st.expander("ℹ️ Multi-Agent Architecture"):
            st.markdown("""
            **Dual-Agent Pipeline Workflow:**
            1. **Input**: Product Concept, Target Domain, Scope Constraints.
            2. **RAG Step 1**: ChromaDB retrieves PRD standards & persona guidelines.
            3. **BA Agent**: Analyzes problem space & constructs 2 rich user personas.
            4. **RAG Step 2**: ChromaDB retrieves NFR metrics & risk matrices.
            5. **PM Agent**: Generates INVEST user stories, MoSCoW functional specs, NFRs & risk matrix.
            6. **Dedicated Results Page**: Multi-tab view, quality analytics & multi-format export.
            """)

    # Route to active view
    if st.session_state["current_view"] == "results":
        render_results_page()
    else:
        render_input_page(env_key, selected_model, selected_preset)


if __name__ == "__main__":
    main()
