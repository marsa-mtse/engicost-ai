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
    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 0.5rem; animation: fadeInUp 0.5s ease-out;">
        <div style="font-size: 2.5rem; text-shadow: 0 0 20px rgba(14,165,233,0.5);">{icon}</div>
        <h2 style="margin: 0; font-size: 2rem; font-weight: 800; background: linear-gradient(90deg, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{title}</h2>
    </div>
    <div style="height: 2px; width: 100%; background: linear-gradient(90deg, rgba(56,189,248,0.5), transparent); margin-bottom: 2rem; border-radius: 2px;"></div>
    """, unsafe_allow_html=True)

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
        --sidebar-bg: rgba(7, 10, 19, 0.85); /* More transparent for blur */
        --card-bg: rgba(30, 41, 59, 0.45);
        --accent-primary: #0ea5e9;
        --accent-secondary: #6366f1;
        --accent-glow: rgba(14, 165, 233, 0.2);
        --text-primary: #f8fafc;
        --text-secondary: #94a3b8;
        --text-muted: #64748b;
        --success: #10b981;
        --danger: #ef4444;
        --glass-border: rgba(255, 255, 255, 0.08);
        --glass-border-strong: rgba(255, 255, 255, 0.15);
        --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
        --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
        --shadow-lg: 0 10px 30px -5px rgba(0, 0, 0, 0.3);
    }

    /* Modern Fade-in & Mesh Animations */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes float {
        0% { transform: translateY(0px) rotate(0deg); }
        50% { transform: translateY(-10px) rotate(1deg); }
        100% { transform: translateY(0px) rotate(0deg); }
    }

    @keyframes meshBg {
        0% { background-position: 0% 0%; }
        50% { background-position: 100% 100%; }
        100% { background-position: 0% 0%; }
    }
    
    @keyframes pulseGlow {
        0% { box-shadow: 0 0 0 0 var(--accent-glow); }
        70% { box-shadow: 0 0 0 15px rgba(14,165,233, 0); }
        100% { box-shadow: 0 0 0 0 rgba(14,165,233, 0); }
    }

    .animate-up {
        animation: fadeInUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }

    .stApp {
        background-color: var(--bg-main);
        /* Neo-Glassmorphism Mesh Gradient Background */
        background-image: 
            radial-gradient(circle at 15% 50%, rgba(14, 165, 233, 0.12), transparent 40%),
            radial-gradient(circle at 85% 30%, rgba(99, 102, 241, 0.12), transparent 40%),
            radial-gradient(circle at 50% 100%, rgba(16, 185, 129, 0.08), transparent 40%),
            radial-gradient(circle at 80% 90%, rgba(139, 92, 246, 0.08), transparent 40%);
        background-size: 150% 150%;
        animation: meshBg 20s ease-in-out infinite alternate;
        font-family: 'Outfit', 'Inter', sans-serif !important;
        color: var(--text-primary);
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: var(--sidebar-bg) !important;
        backdrop-filter: blur(30px) saturate(150%);
        -webkit-backdrop-filter: blur(30px) saturate(150%);
        border-right: 1px solid var(--glass-border-strong) !important;
        box-shadow: 5px 0 25px rgba(0,0,0,0.2) !important;
    }
    
    [data-testid="stSidebarNav"] {
        background-color: transparent !important;
    }

    /* Glassmorphism Cards V4 */
    .glass-card {
        background: linear-gradient(145deg, var(--card-bg), rgba(15, 23, 42, 0.7));
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid var(--glass-border);
        border-top: 1px solid rgba(255,255,255,0.15); /* Top highlight for depth */
        border-left: 1px solid rgba(255,255,255,0.05); /* Soft left highlight */
        border-radius: 28px;
        padding: 2rem;
        margin-bottom: 1.5rem;
        transition: all 0.5s cubic-bezier(0.16, 1, 0.3, 1);
        box-shadow: inset 0 1px 0 0 rgba(255,255,255,0.05), var(--shadow-lg);
        position: relative;
        overflow: hidden;
    }
    
    .glass-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        background: linear-gradient(45deg, transparent, rgba(255,255,255,0.03), transparent);
        transform: translateX(-100%);
        transition: 0.6s;
    }

    .glass-card:hover::before {
        transform: translateX(100%);
    }

    .glass-card:hover {
        transform: translateY(-8px) scale(1.02);
        background: linear-gradient(145deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.9));
        border-color: rgba(56, 189, 248, 0.4);
        box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5), 0 0 30px var(--accent-glow);
    }

    /* Premium Buttons V4 */
    .stButton > button {
        border-radius: 16px !important;
        background: linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 100%) !important;
        color: white !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        font-weight: 700 !important;
        padding: 0.75rem 1.5rem !important;
        transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1) !important;
        box-shadow: 0 8px 20px rgba(14, 165, 233, 0.3), inset 0 2px 0 rgba(255,255,255,0.2) !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        position: relative;
        overflow: hidden;
    }

    .stButton > button:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 15px 30px rgba(14, 165, 233, 0.5), inset 0 2px 0 rgba(255,255,255,0.3) !important;
        filter: brightness(1.2);
    }
    
    .stButton > button:active {
        transform: translateY(1px) !important;
        box-shadow: 0 4px 10px rgba(14, 165, 233, 0.2) !important;
    }

    /* Input & Search Styling V4 */
    .stTextInput > div > div > input, .stSelectbox > div > div > div, .stTextArea > div > div > textarea {
        background-color: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 14px !important;
        color: white !important;
        transition: all 0.3s ease !important;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.2);
    }
    
    .stTextInput > div > div > input:focus, .stSelectbox > div > div > div:focus, .stTextArea > div > div > textarea:focus {
        border-color: var(--accent-primary) !important;
        box-shadow: 0 0 0 2px rgba(14, 165, 233, 0.2), inset 0 2px 4px rgba(0,0,0,0.1) !important;
        background-color: rgba(15, 23, 42, 0.8) !important;
    }

    /* AI BRIDGE - Floating Action Button */
    .floating-ai-bridge {
        position: fixed;
        bottom: 35px;
        right: 35px;
        z-index: 999990 !important;
        animation: float 5s ease-in-out infinite;
    }
    
    .floating-ai-bridge button {
        width: 70px !important;
        height: 70px !important;
        min-width: 70px !important;
        border-radius: 50% !important;
        padding: 0 !important;
        background: linear-gradient(135deg, #38bdf8, #6366f1) !important;
        border: 2px solid rgba(255,255,255,0.4) !important;
        box-shadow: 0 10px 30px rgba(14, 165, 233, 0.6) !important;
        font-size: 32px !important;
        transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }
    
    .floating-ai-bridge button:hover {
        transform: scale(1.1) rotate(5deg) !important;
        box-shadow: 0 20px 40px rgba(14, 165, 233, 0.8), 0 0 20px rgba(255,255,255,0.4) !important;
        animation: pulseGlow 1.5s infinite;
    }

    /* Mobile Optimization */
    @media (max-width: 768px) {
        .glass-card { padding: 1.5rem; border-radius: 20px; }
        .ai-bridge { bottom: 20px; right: 20px; width: 60px; height: 60px; }
    }
    </style>
    """
