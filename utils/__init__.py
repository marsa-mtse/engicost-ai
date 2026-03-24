import streamlit as st
import sys
import os

def is_stlite():
    """Detect if running in stlite (browser-side) environment."""
    return sys.platform == "emscripten" or os.environ.get("STLITE_URL") is not None

def inject_react_translation_fix():
    """Injects a global JS patch to prevent React 'removeChild' Node errors caused by Google Translate."""
    import streamlit.components.v1 as components
    components.html("""
        <script>
        const patch = () => {
            const parent = window.parent;
            if (!parent || !parent.Node || parent.window.reactTranslatePatched) return;
            
            parent.window.reactTranslatePatched = true;
            console.log('[EngiCost] Applying React DOM Translation Guard...');

            const originalRemoveChild = parent.Node.prototype.removeChild;
            parent.Node.prototype.removeChild = function(child) {
                if (child.parentNode !== this) {
                    console.warn('[EngiCost] Prevented removeChild crash:', child, 'is not a child of', this);
                    return child; 
                }
                return originalRemoveChild.apply(this, arguments);
            };

            const originalInsertBefore = parent.Node.prototype.insertBefore;
            parent.Node.prototype.insertBefore = function(newNode, referenceNode) {
                if (referenceNode && referenceNode.parentNode !== this) {
                    console.warn('[EngiCost] Prevented insertBefore crash:', referenceNode, 'is not a child of', this);
                    return newNode;
                }
                return originalInsertBefore.apply(this, arguments);
            };
        };
        // Run immediately and also on a slight delay to ensure parent is ready
        patch();
        setTimeout(patch, 500);
        setTimeout(patch, 2000);
        </script>
    """, height=0, width=0)

def t(ar_text, en_text):
    """
    Multilingual text helper. English or Arabic based on selection.
    """
    lang = st.session_state.get("lang", "ar")
    if lang == "en":
        return en_text
    return ar_text

def render_section_header(title, icon=""):
    """Render a styled section header for the app."""
    st.markdown(f"### {icon} {title}")
    st.markdown("---")

def generate_wa_link(text: str, phone: str = "") -> str:
    """Generate a pre-filled WhatsApp wa.me link."""
    from urllib.parse import quote
    base = f"https://wa.me/{phone}" if phone else "https://wa.me/"
    return f"{base}?text={quote(text)}"

def check_api_keys():
    """Check if essential AI API keys are configured."""
    from config import GEMINI_API_KEY, GROQ_API_KEY
    missing = []
    if not GEMINI_API_KEY: missing.append("GEMINI_API_KEY")
    if not GROQ_API_KEY: missing.append("GROQ_API_KEY")
    return missing

@st.cache_data
def get_theme_css():
    """Return 'World-Class' styling for the EngiCost AI platform."""
    return """
    <style>
    /* PWA & Mobile Optimization */
    @viewport { width: device-width; zoom: 1.0; }
    
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');

    :root {
        --bg-main: #020617;
        --sidebar-bg: rgba(7, 10, 19, 0.98);
        --card-bg: rgba(30, 41, 59, 0.4);
        --accent-primary: #0ea5e9;
        --accent-secondary: #6366f1;
        --accent-glow: rgba(14, 165, 233, 0.15);
        --text-primary: #f8fafc;
        --text-secondary: #94a3b8;
        --text-muted: #64748b;
        --success: #10b981;
        --danger: #ef4444;
        --glass-border: rgba(255, 255, 255, 0.08);
        --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
        --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
        --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
    }

    /* Modern Fade-in Animation */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(15px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes float {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
        100% { transform: translateY(0px); }
    }

    .animate-up {
        animation: fadeInUp 0.7s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards;
    }

    .stApp {
        background-color: var(--bg-main);
        background-image: 
            radial-gradient(at 10% 10%, rgba(14, 165, 233, 0.1) 0px, transparent 50%),
            radial-gradient(at 90% 90%, rgba(99, 102, 241, 0.1) 0px, transparent 50%);
        font-family: 'Outfit', 'Inter', sans-serif !important;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: var(--sidebar-bg) !important;
        backdrop-filter: blur(25px);
        border-right: 1px solid var(--glass-border) !important;
    }
    
    [data-testid="stSidebarNav"] {
        background-color: transparent !important;
    }

    /* Glassmorphism Cards */
    .glass-card {
        background: var(--card-bg);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid var(--glass-border);
        border-radius: 24px;
        padding: 1.7rem;
        margin-bottom: 1.5rem;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: var(--shadow-md);
    }
    
    .glass-card:hover {
        transform: translateY(-8px) scale(1.01);
        background: rgba(30, 41, 59, 0.6);
        border-color: var(--accent-primary);
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4), 0 0 20px var(--accent-glow);
    }

    /* Premium Buttons */
    .stButton > button {
        border-radius: 14px !important;
        background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary)) !important;
        color: white !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        font-weight: 700 !important;
        padding: 0.6rem 1.2rem !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 15px rgba(14, 165, 233, 0.3) !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(14, 165, 233, 0.5) !important;
        filter: brightness(1.15);
    }

    /* Input & Search Styling */
    .stTextInput > div > div > input, .stSelectbox > div > div > div {
        background-color: rgba(15, 23, 42, 0.5) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: 12px !important;
        color: white !important;
    }
    
    /* AI BRIDGE - Native Streamlit Button Style */
    .floating-ai-bridge {
        position: fixed;
        bottom: 30px;
        right: 30px;
        z-index: 999990 !important;
        animation: float 4s ease-in-out infinite;
    }
    
    .floating-ai-bridge button {
        width: 65px !important;
        height: 65px !important;
        min-width: 65px !important;
        border-radius: 50% !important;
        padding: 0 !important;
        background: linear-gradient(135deg, #0ea5e9, #6366f1) !important;
        border: 2px solid rgba(255,255,255,0.3) !important;
        box-shadow: 0 10px 30px rgba(14, 165, 233, 0.5) !important;
        font-size: 28px !important;
        transition: all 0.3s ease !important;
    }
    
    .floating-ai-bridge button:hover {
        transform: scale(1.15) !important;
        box-shadow: 0 15px 40px rgba(14, 165, 233, 0.7) !important;
        filter: brightness(1.1);
    }

    /* Global Search Box in Sidebar */
    .global-search-container {
        padding: 0 1rem 1rem 1rem;
    }

    /* Mobile Optimization */
    @media (max-width: 768px) {
        .glass-card { padding: 1.2rem; }
        .ai-bridge { bottom: 20px; right: 20px; width: 55px; height: 55px; }
    }
    </style>
    """
