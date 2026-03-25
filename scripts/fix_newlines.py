import sys

with open(r'd:\engicost-ai\views\drawing_engine_view.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = r"""                        try:\n                            from ai_engine.drawing_brain import extract_quantities_from_plan\n                            if "floors" not in r_data: r_data["floors"] = floor_count\n                            transfer_text = extract_quantities_from_plan(r_data, specialty)\n                        except Exception as e:\n                            transfer_text = f"Extraction Error: {e}"\n                        st.session_state.boq_transfer_data = transfer_text"""

replacement = """                        try:
                            from ai_engine.drawing_brain import extract_quantities_from_plan
                            if "floors" not in r_data: r_data["floors"] = floor_count
                            transfer_text = extract_quantities_from_plan(r_data, specialty)
                        except Exception as e:
                            transfer_text = f"Extraction Error: {e}"
                        st.session_state.boq_transfer_data = transfer_text"""

if target in text:
    new_text = text.replace(target, replacement)
    with open(r'd:\engicost-ai\views\drawing_engine_view.py', 'w', encoding='utf-8') as f:
        f.write(new_text)
    print('SUCCESS')
else:
    print('TARGET NOT FOUND')
