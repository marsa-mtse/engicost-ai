import streamlit as st
import time
from utils import t, render_section_header
from ai_engine.cost_engine import get_cost_engine

def render_ai_assistant():
    render_section_header(t("المساعد الهندسي الذكي", "Smart Engineering Assistant"), "🤖")
    
    st.markdown(f"""
    <div class="glass-card animate-up">
        <p style="color:var(--text-muted);">
            {t("اسأل المساعد الذكي عن أي شيء يخص تكاليف البناء، المواصفات الفنية، الأكواد الهندسية (ECP)، عقود الفيديك، وأنظمة الكهروميكانيك MEP.", 
               "Ask the smart assistant anything about construction costs, technical specs, Engineering Codes (ECP), FIDIC, and MEP systems.")}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # --- Expert Role Selection ---
    col1, col2 = st.columns([1, 3])
    with col1:
        expert_role = st.selectbox(
            t("تخصص المساعد", "Assistant Expertise"),
            options=[
                t("مهندس استشاري شامل (عام)", "General Consulting Engineer"),
                t("مهندس مدني وإنشائي (ECP)", "Civil & Structural Engineer (ECP)"),
                t("مهندس كهروميكانيك (MEP)", "MEP Engineer"),
                t("خبير عقود ومناقصات (FIDIC)", "Contracts & Tenders Expert (FIDIC)"),
                t("خبير تسعير وحصر كميات", "QS & Cost Estimator")
            ]
        )
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑️ " + t("مسح المحادثة", "Clear Chat"), key="clear_chat"):
            st.session_state.messages = []
            st.rerun()

    st.markdown("---")

    # Chat History
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # React to user input
    if prompt := st.chat_input(t("كيف يمكنني مساعدتك اليوم؟", "How can I help you today?")):
        # Display user message in chat message container
        st.chat_message("user").markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            with st.spinner(t("جاري التفكير...", "Thinking...")):
                try:
                    from ai_engine.market_api import MarketEngine
                    engine = get_cost_engine()
                    
                    # Fetch real-time market context to ensure accuracy
                    market_data = MarketEngine.get_live_prices()
                    currency = st.session_state.get("currency", "USD")
                    region = st.session_state.get("region", "Global")
                    
                    usd_ctx = "\n".join([f"- {k}: ${v:,.2f}" for k, v in market_data['usd'].items()])
                    local_ctx = "\n".join([f"- {k}: {v:,.2f} {currency}" for k, v in market_data['local'].items()])
                    rate = market_data['rate']
                    
                    # Parse conversation history for context
                    history_context = ""
                    if len(st.session_state.messages) > 1: # More than just the current prompt
                        history_context = "--- PREVIOUS CONVERSATION HISTORY ---\n"
                        for msg in st.session_state.messages[-6:-1]: # Last 5 messages for context
                            role_mark = "USER" if msg["role"] == "user" else "ASSISTANT"
                            history_context += f"{role_mark}: {msg['content']}\n"
                        history_context += "--------------------------------------\n\n"
                    
                    # Custom prompt for the assistant
                    chat_prompt = f"""You are 'EngiCost AI', an elite expert in engineering and construction in {region}, specifically acting as: {expert_role}.
                    Your knowledge covers all engineering disciplines including Civil, Architectural, MEP (HVAC, Fire, Plumbing, Electrical), FIDIC contracts, and local Engineering Codes of Practice (if applicable like ECP or Saudi Building Code).
                    
                    CURRENT MARKET CONTEXT (TODAY):
                    Exchange Rate: 1 USD = {rate:.2f} {currency}
                    
                    PRICES IN {currency}:
                    {local_ctx}
                    
                    {history_context}
                    
                    NEW USER QUESTION: {prompt}
                    
                    Instructions for your response:
                    1. Respond professionally in Arabic (unless the user asks in English).
                    2. Act strictly as the selected expert ({expert_role}). Provide detailed, technically accurate, engineering-grade advice suitable for {region}.
                    3. If the user asks about Building Codes, cite the relevant local code sections if possible.
                    4. If the user asks about MEP systems (water stations, fire protection, HVAC, electrical), provide comprehensive system breakdowns.
                    5. Use the {currency} prices for any price-related questions by default.
                    6. If explaining a process, use bullet points or numbered lists.
                    7. If the user asks about prices or specifications, present the data in a CLEAR ORGANIZED MARKDOWN TABLE with {currency} and USD equivalents.
                    """
                    # We reuse the _call_groq or _call_gemini_text for chat
                    # For simplicity, we'll try a basic call
                    response_text, err = engine._call_groq(chat_prompt, expect_json=False)
                    if not response_text:
                        response_text, err = engine._call_gemini_text(chat_prompt, expect_json=False)
                    
                    if isinstance(response_text, (list, dict)):
                         response_text = str(response_text)
                    
                    if not response_text:
                        response_text = t("عذراً، واجهت مشكلة في الاتصال بمحرك الذكاء الاصطناعي.", "Sorry, I encountered an issue connecting to the AI engine.")

                except Exception as e:
                    response_text = f"Error: {e}"

            # Display response
            if "|" in response_text and "---" in response_text:
                # If it's a table, skip streaming to preserve formatting during render
                message_placeholder.markdown(response_text)
            else:
                # Simulate streaming response
                for chunk in response_text.split():
                    full_response += chunk + " "
                    time.sleep(0.04)
                    message_placeholder.markdown(full_response + "▌")
                message_placeholder.markdown(full_response)
            
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": full_response})
