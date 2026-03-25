import sys
import re

with open(r'd:\engicost-ai\app.py', 'r', encoding='utf-8') as f:
    text = f.read()

pattern = re.compile(r'    try:\s+if current_key == "dashboard":.*?(?=    except Exception as e:)', re.DOTALL)

replacement = """    VIEW_ROUTER = {
        "dashboard": ("views.dashboard_view", "render_dashboard"),
        "admin": ("views.admin_view", "render_admin_panel"),
        "market": ("views.forecasting_view", "render_forecasting"),
        "tender": ("views.tender_hub_view", "render_tender_hub"),
        "assistant": ("views.ai_assistant_view", "render_ai_assistant"),
        "blueprint": ("views.blueprint_view", "render_blueprint_analysis"),
        "fidic": ("views.fidic_scanner_view", "render_fidic_scanner"),
        "fidic_letters": ("views.fidic_letters_view", "render_fidic_generator"),
        "boq": ("views.boq_view", "render_boq_pricing"),
        "compare": ("views.compare_view", "render_boq_comparison"),
        "profit": ("views.profit_calculator_view", "render_profit_calculator"),
        "structural": ("views.structural_calc_view", "render_structural_calc"),
        "bbs": ("views.bbs_view", "render_bbs_assistant"),
        "mep": ("views.mep_view", "render_mep_systems"),
        "gantt": ("views.gantt_view", "render_gantt_progress"),
        "drafting": ("views.drawing_engine_view", "render_drawing_engine"),
        "survey": ("views.survey_view", "render_survey_management"),
        "ipc": ("views.ipc_view", "render_ipc_invoice"),
        "suppliers": ("views.suppliers_view", "render_suppliers"),
        "qaqc": ("views.qaqc_view", "render_qaqc"),
        "collab": ("views.collaboration_view", "render_collaboration"),
        "workspace": ("views.workspace_view", "render_workspace"),
        "billing": ("views.billing_view", "render_billing"),
        "inventory": ("views.inventory_view", "render_inventory_management"),
        "finance": ("views.finance_view", "render_financial_analysis"),
        "hr": ("views.hr_view", "render_hr_management"),
        "assets": ("views.assets_view", "render_assets_management"),
        "settings": ("views.settings_view", "render_settings"),
        "legal": ("views.legal_view", "render_legal"),
        "brain": ("views.ai_brain_view", "render_ai_brain"),
    }

    try:
        if current_key in VIEW_ROUTER:
            import importlib
            mod_name, func_name = VIEW_ROUTER[current_key]
            module = importlib.import_module(mod_name)
            getattr(module, func_name)()
"""

new_text, count = pattern.subn(replacement, text)

if count > 0:
    with open(r'd:\engicost-ai\app.py', 'w', encoding='utf-8') as f:
        f.write(new_text)
    print("SUCCESS: REPLACED APP.PY ROUTER")
else:
    print("FAILED: REGEX DID NOT MATCH")
