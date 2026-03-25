"""
EngiCost AI — RAG Brain Engine (Retrieval-Augmented Generation)
================================================================
Searches local engineering knowledge base and enriches Groq/Gemini prompts
with relevant context for highly accurate, cited answers.

Strategy: TF-IDF-style keyword overlap scoring (no external vector DB needed).
          Works entirely offline and on Streamlit Cloud.
"""

import json
import os
import re
import math
from typing import List, Dict, Tuple, Optional

try:
    from utils import t
except Exception:
    def t(a, e): return a


# ── Knowledge Base Loader ─────────────────────────────────────────────────────

_KB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "knowledge")
_LOADED_KB: Dict[str, any] = {}


def _load_kb(filename: str) -> dict:
    """Load and cache a knowledge base JSON file."""
    if filename in _LOADED_KB:
        return _LOADED_KB[filename]
    path = os.path.join(_KB_DIR, filename)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            _LOADED_KB[filename] = data
            return data
    except Exception as e:
        print(f"[RAG] Warning: could not load {filename}: {e}")
        return {}


# ── Text Preprocessing ────────────────────────────────────────────────────────

def _tokenize(text: str) -> List[str]:
    """Simple tokenizer: lowercase Arabic+English words, remove punctuation."""
    text = text.lower()
    # Keep Arabic and English letters and digits
    tokens = re.findall(r'[\u0600-\u06ff0-9a-z]+', text)
    return [t for t in tokens if len(t) > 1]


def _score_overlap(query_tokens: List[str], text: str) -> float:
    """
    Score a candidate text against query tokens using term overlap.
    Returns a value 0.0 - 1.0.
    """
    if not text or not query_tokens:
        return 0.0
    text_tokens = set(_tokenize(text))
    q_set = set(query_tokens)
    overlap = len(q_set & text_tokens)
    if overlap == 0:
        return 0.0
    # Jaccard-like score with query length normalization
    return overlap / (len(q_set) + math.log(len(text_tokens) + 1))


# ── Knowledge Retrieval ────────────────────────────────────────────────────────

def _search_faqs(query_tokens: List[str], top_k: int = 3) -> List[Dict]:
    """Search the FAQ knowledge base."""
    kb = _load_kb("faqs.json")
    results = []
    for faq in kb.get("faqs", []):
        # Score against question + keywords
        text_to_score = " ".join([
            faq.get("question_ar", ""),
            faq.get("question_en", ""),
            " ".join(faq.get("keywords", []))
        ])
        score = _score_overlap(query_tokens, text_to_score)
        if score > 0:
            results.append({"type": "faq", "score": score, "data": faq})

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


def _search_prices(query_tokens: List[str], top_k: int = 5) -> List[Dict]:
    """Search the prices knowledge base."""
    kb = _load_kb("prices.json")
    results = []
    for cat_key, category in kb.get("categories", {}).items():
        for item in category.get("items", []):
            text_to_score = " ".join([
                item.get("name_ar", ""),
                item.get("name_en", ""),
                category.get("label_ar", ""),
                category.get("label_en", ""),
                item.get("note", "")
            ])
            score = _score_overlap(query_tokens, text_to_score)
            if score > 0:
                results.append({
                    "type": "price",
                    "score": score,
                    "data": item,
                    "category": category.get("label_ar", cat_key)
                })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


def _search_ecp_codes(query_tokens: List[str], top_k: int = 3) -> List[Dict]:
    """Search the ECP building codes knowledge base."""
    kb = _load_kb("ecp_codes.json")
    results = []
    for section_key, section in kb.get("sections", {}).items():
        for rule in section.get("rules", []):
            text_to_score = " ".join([
                rule.get("rule_ar", ""),
                rule.get("rule_en", ""),
                section.get("title_ar", ""),
                section.get("title_en", "")
            ])
            score = _score_overlap(query_tokens, text_to_score)
            if score > 0:
                results.append({
                    "type": "ecp_rule",
                    "score": score,
                    "data": rule,
                    "section": section.get("title_ar", section_key)
                })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


def _search_boq_templates(query_tokens: List[str], top_k: int = 2) -> List[Dict]:
    """Search BOQ templates knowledge base."""
    kb = _load_kb("boq_templates.json")
    results = []
    for tmpl in kb.get("templates", []):
        text_to_score = " ".join([
            tmpl.get("name_ar", ""),
            tmpl.get("name_en", ""),
            " ".join(tmpl.get("keywords", [])),
            tmpl.get("scope", "")
        ])
        score = _score_overlap(query_tokens, text_to_score)
        if score > 0:
            results.append({"type": "template", "score": score, "data": tmpl})

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


def _search_user_docs(query_tokens: List[str], top_k: int = 5) -> List[Dict]:
    """Search documents uploaded by the user in this session."""
    import streamlit as st
    results = []
    
    # User docs are expected to be in st.session_state as a list of dicts
    user_docs = st.session_state.get("user_docs", [])
    if not user_docs:
        return []

    for doc in user_docs:
        content = doc.get("content", "")
        score = _score_overlap(query_tokens, content)
        if score > 0:
            results.append({
                "type": "user_doc",
                "score": score,
                "data": doc
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


def process_uploaded_file(uploaded_file) -> Optional[Dict]:
    """Extract text from PDF, TXT, or MD files for RAG indexing."""
    import io
    content = ""
    fname = uploaded_file.name
    
    try:
        if fname.endswith(".pdf"):
            import PyPDF2
            reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.getvalue()))
            for page in reader.pages:
                content += (page.extract_text() or "") + "\n"
        elif fname.endswith((".txt", ".md")):
            content = str(uploaded_file.getvalue(), "utf-8")
        else:
            return None
            
        if not content.strip():
            return None
            
        return {
            "title": fname,
            "content": content,
            "source": f"Uploaded: {fname}",
            "tokens": _tokenize(content)
        }
    except Exception as e:
        print(f"Error processing {fname}: {e}")
        return None


# ── Context Builder ────────────────────────────────────────────────────────────

def retrieve_context(query: str, lang: str = "ar") -> Tuple[str, List[Dict]]:
    """
    Main RAG retrieval function.
    Returns: (context_string_for_prompt, list_of_sources_for_display)
    """
    query_tokens = _tokenize(query)
    if len(query_tokens) < 1:
        return "", []

    all_results = []

    # Search all knowledge bases
    faqs = _search_faqs(query_tokens, top_k=3)
    prices = _search_prices(query_tokens, top_k=4)
    codes = _search_ecp_codes(query_tokens, top_k=3)
    templates = _search_boq_templates(query_tokens, top_k=2)
    
    # --- New: Search User Documents (Uploaded in session) ---
    user_docs = _search_user_docs(query_tokens, top_k=5)

    all_results.extend(faqs)
    all_results.extend(prices)
    all_results.extend(codes)
    all_results.extend(templates)
    all_results.extend(user_docs)

    # Sort globally by score, take top results
    all_results.sort(key=lambda x: x["score"], reverse=True)
    top_results = [r for r in all_results if r["score"] > 0.05][:10]

    if not top_results:
        return "", []

    # Build context string to inject in prompt
    kb_date = "مارس 2026"
    context_lines = [
        f"=== قاعدة المعرفة الهندسية المتخصصة (EngiCost Knowledge Base — {kb_date}) ===\n"
    ]
    sources_for_display = []

    for i, result in enumerate(top_results):
        rtype = result["type"]
        data = result["data"]

        if rtype == "faq":
            context_lines.append(
                f"📌 سؤال شائع:\n"
                f"  السؤال: {data.get('question_ar', '')}\n"
                f"  الإجابة: {data.get('answer_ar', '')}\n"
                f"  المصدر: {data.get('source', 'قاعدة المعرفة')}\n"
            )
            sources_for_display.append({
                "icon": "❓",
                "title": data.get("question_ar", ""),
                "type": "FAQ",
                "source": data.get("source", ""),
                "score": result["score"]
            })

        elif rtype == "price":
            item = data
            price_info = (
                f"  السعر: {item.get('price_avg', '?'):,} جنيه/{item.get('unit', '')} "
                f"(نطاق: {item.get('price_min', '?'):,} - {item.get('price_max', '?'):,})"
            )
            context_lines.append(
                f"💰 سعر: {item.get('name_ar', '')}\n"
                f"{price_info}\n"
                f"  الفئة: {result.get('category', '')}\n"
                f"  ملاحظة: {item.get('note', 'لا توجد')}\n"
            )
            sources_for_display.append({
                "icon": "💰",
                "title": item.get("name_ar", ""),
                "type": "سعر سوق 2026",
                "source": f"prices.json — {result.get('category', '')}",
                "score": result["score"]
            })

        elif rtype == "ecp_rule":
            rule = data
            context_lines.append(
                f"📐 كود بناء (ECP 203):\n"
                f"  {rule.get('rule_ar', '')}\n"
                f"  المرجع: {rule.get('reference', '')}\n"
            )
            sources_for_display.append({
                "icon": "📐",
                "title": rule.get("rule_ar", "")[:60] + "...",
                "type": "كود بناء ECP",
                "source": rule.get("reference", "ECP 203"),
                "score": result["score"]
            })

        elif rtype == "template":
            tmpl = data
            item_names = [it.get("item", "") for it in tmpl.get("items", [])[:5]]
            context_lines.append(
                f"📋 قالب مقايسة: {tmpl.get('name_ar', '')}\n"
                f"  النطاق: {tmpl.get('scope', '')}\n"
                f"  البنود الرئيسية: {', '.join(item_names)}\n"
            )
            sources_for_display.append({
                "icon": "📋",
                "title": tmpl.get("name_ar", ""),
                "type": "قالب مقايسة",
                "source": "boq_templates.json",
                "score": result["score"]
            })

        elif rtype == "user_doc":
            doc = data
            context_lines.append(
                f"📄 مستند مستخدم ({doc.get('title', 'تحليل')}):\n"
                f"  {doc.get('content', '')[:1000]}\n" # limit context size
            )
            sources_for_display.append({
                "icon": "📄",
                "title": doc.get('title', 'مستند خارجي'),
                "type": "مستند مستخدم",
                "source": doc.get('source', 'رفع يدوي'),
                "score": result["score"]
            })

    context_string = "\n".join(context_lines)
    context_string += "\n=== نهاية قاعدة المعرفة ===\n"

    return context_string, sources_for_display


def build_rag_prompt(query: str, context: str, lang: str = "ar") -> str:
    """
    Build a full RAG-enhanced prompt for the LLM.
    """
    if lang == "en":
        system_part = (
            "You are EngiCost AI Brain — an expert engineering assistant specialized in "
            "Egyptian construction and engineering. Use the knowledge base context below "
            "to answer accurately. Cite prices as '2026 market rate'. "
            "ECP 203 codes should be quoted precisely. "
            "If the context doesn't have enough info, say so and recommend professional consultation."
        )
    else:
        system_part = (
            "أنت العقل الهندسي لمنصة EngiCost AI — خبير هندسي متخصص في قطاع الإنشاء المصري. "
            "استخدم قاعدة المعرفة أدناه للإجابة بدقة واحترافية. "
            "عند ذكر الأسعار أشر إلى أنها 'أسعار السوق المصري مارس 2026'. "
            "اقتبس بنود كود ECP 203 بدقة عند الحاجة. "
            "إذا لم تجد المعلومة في قاعدة المعرفة، قل ذلك صراحةً وانصح بمراجعة مهندس مختص."
        )

    if context:
        prompt = f"{system_part}\n\n{context}\n\nسؤال المستخدم: {query}"
    else:
        prompt = f"{system_part}\n\nسؤال المستخدم: {query}"

    return prompt


def get_template_for_project(project_description: str) -> Optional[Dict]:
    """
    Find the most relevant BOQ template for a project description.
    Used by AI-to-BOQ auto-generator.
    """
    kb = _load_kb("boq_templates.json")
    query_tokens = _tokenize(project_description)
    best_match = None
    best_score = 0.0

    for tmpl in kb.get("templates", []):
        text_to_score = " ".join([
            tmpl.get("name_ar", ""),
            tmpl.get("name_en", ""),
            " ".join(tmpl.get("keywords", []))
        ])
        score = _score_overlap(query_tokens, text_to_score)
        if score > best_score:
            best_score = score
            best_match = tmpl

    return best_match if best_score > 0.05 else None
