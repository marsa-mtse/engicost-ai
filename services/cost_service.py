import json
from typing import List, Dict, Any, Optional

class CostService:
    @staticmethod
    def calculate_tender_price(
        direct_costs: float, 
        overhead_pct: float, 
        contingency_pct: float, 
        profit_pct: float, 
        vat_pct: float
    ) -> Dict[str, float]:
        """Calculates final tender price components based on percentages."""
        overhead_val    = direct_costs * overhead_pct / 100
        contingency_val = direct_costs * contingency_pct / 100
        subtotal        = direct_costs + overhead_val + contingency_val
        profit_val      = subtotal * profit_pct / 100
        pre_vat         = subtotal + profit_val
        vat_val         = pre_vat * vat_pct / 100
        grand_total     = pre_vat + vat_val

        return {
            "direct_cost": direct_costs,
            "overhead_val": overhead_val,
            "contingency_val": contingency_val,
            "subtotal": subtotal,
            "profit_val": profit_val,
            "pre_vat": pre_vat,
            "vat_val": vat_val,
            "grand_total": grand_total
        }

    @staticmethod
    def match_boq_items(engine, items: List[Dict], prices: Dict, currency: str, rate: float) -> List[Dict]:
        """
        Smart matching logic using AI to correlate BOQ items with market prices.
        'engine' should be a CostEngine instance.
        """
        if not items:
            return []

        # Prepare context
        market_context_egp = {k: v.get('egp', v) if isinstance(v, dict) else v for k, v in prices.items()}
        
        # Simple string matching or AI-based matching
        # For 'Highest Version', we use the engine's AI capabilities
        try:
            items_json = json.dumps(items)
            match_prompt = f"""
            Match these BOQ items to the current market prices.
            Market Prices (EGP): {json.dumps(market_context_egp)}
            Items to match: {items_json}
            
            Return a JSON dictionary where key is the index and value is the best matched EGP price per unit.
            If no match, estimate a realistic price based on item complexity.
            Return ONLY the JSON.
            """
            match_res, _ = engine._call_groq(match_prompt, expect_json=True)
            if not match_res:
                 match_res, _ = engine._call_gemini_text(match_prompt, expect_json=True)
            
            if match_res:
                for i, item in enumerate(items):
                    idx_str = str(i)
                    if idx_str in match_res:
                        p_egp = float(match_res[idx_str])
                        # Convert to requested currency
                        item['rate'] = p_egp if currency == "EGP" else p_egp / rate
            return items
        except Exception as e:
            print(f"Match error: {e}")
            return items

    @staticmethod
    def save_project(db_session, user_id: int, name: str, project_type: str, data: List[Dict]):
        """Persist project to DB."""
        from database import Project
        import datetime
        new_proj = Project(
            owner_id=user_id,
            name=name,
            project_type=project_type,
            result_data=json.dumps(data),
            created_at=datetime.datetime.utcnow(),
        )
        db_session.add(new_proj)
        db_session.commit()
        return new_proj
