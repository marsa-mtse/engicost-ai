import os

def apply_fix():
    file_path = r'd:\engicost-ai\views\dashboard_view.py'
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()

    target = """                                col_a, col_b = st.columns(2)
                                with col_a:
                                    excel_data = ExportEngine.generate_professional_excel(df_show)
                                    st.download_button(t("📊 Excel", "Excel"), data=excel_data, file_name=f"{p.name}.xlsx", key=f"ex_{p.id}")
                                with col_b:
                                    pdf_data = ExportEngine.generate_professional_pdf(df_show, project_name=p.name)
                                    st.download_button(t("📄 PDF", "PDF"), data=pdf_data, file_name=f"{p.name}.pdf", key=f"pd_{p.id}")"""

    replacement = """                                col_a, col_b, col_c = st.columns(3)
                                with col_a:
                                    excel_data = ExportEngine.generate_professional_excel(df_show)
                                    st.download_button(t("📊 Excel", "Excel"), data=excel_data, file_name=f"{p.name}.xlsx", key=f"ex_{p.id}", use_container_width=True)
                                with col_b:
                                    pdf_data = ExportEngine.generate_professional_pdf(df_show, project_name=p.name)
                                    st.download_button(t("📄 PDF", "PDF"), data=pdf_data, file_name=f"{p.name}.pdf", key=f"pd_{p.id}", use_container_width=True)
                                with col_c:
                                    if st.button(t("🔗 إنشاء رابط مشاركة", "🔗 Share Link"), key=f"sh_{p.id}", use_container_width=True):
                                        from database import SessionLocal, Project
                                        import uuid
                                        db = SessionLocal()
                                        try:
                                            db_p = db.query(Project).get(p.id)
                                            if not db_p.share_token:
                                                db_p.share_token = str(uuid.uuid4())
                                                db_p.is_public = True
                                                db.commit()
                                            st.session_state[f"share_link_{p.id}"] = db_p.share_token
                                        finally:
                                            db.close()
                                
                                tk = st.session_state.get(f"share_link_{p.id}")
                                if tk:
                                    st.info(t(f"**رابط العميل المباشر:**\\n`https://engicost-ai.streamlit.app/?share={tk}`", f"**Client Link:**\\n`https://engicost-ai.streamlit.app/?share={tk}`"))"""

    if target in text:
        new_text = text.replace(target, replacement)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_text)
        print("SUCCESS")
    else:
        print("TARGET NOT FOUND")

if __name__ == '__main__':
    apply_fix()
