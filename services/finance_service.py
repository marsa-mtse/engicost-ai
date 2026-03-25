import json
import datetime
from typing import Dict, Any
from database import InventoryItem, MaterialTransaction, Expense, Project

class FinanceService:
    @staticmethod
    def get_project_financials(db, project_id: int) -> Dict[str, Any]:
        project = db.query(Project).get(project_id)
        if not project:
            return {"error": "Project not found"}
            
        # 1. Planned Budget (from BOQ)
        planned_total = 0
        if project.project_type == "BOQ" and project.result_data:
            try:
                res_data = json.loads(project.result_data)
                if isinstance(res_data, list):
                    for row in res_data:
                        total_str = str(row.get("Total Cost", "0")).replace(",", "")
                        try: planned_total += float(total_str)
                        except: pass
            except: pass
            
        # 2. Actual Material Spending
        mat_spending = db.query(MaterialTransaction).join(InventoryItem).filter(
            InventoryItem.project_id == project_id,
            MaterialTransaction.type == "IN"
        ).all()
        actual_mat_cost = sum(t.quantity * (t.unit_price or 0) for t in mat_spending)
        
        # 3. General Expenses
        expenses = db.query(Expense).filter(Expense.project_id == project_id).all()
        actual_gen_cost = sum(e.amount for e in expenses)
        
        actual_total = actual_mat_cost + actual_gen_cost
        profit = planned_total - actual_total
        profit_pct = (profit / planned_total * 100) if planned_total > 0 else 0
        
        return {
            "planned_budget": planned_total,
            "actual_material_cost": actual_mat_cost,
            "actual_general_cost": actual_gen_cost,
            "actual_total": actual_total,
            "profit": profit,
            "profit_pct": profit_pct
        }

    @staticmethod
    def log_expense(db, project_id: int, category: str, amount: float, description: str):
        new_exp = Expense(
            project_id=project_id,
            category=category,
            amount=amount,
            description=description
        )
        db.add(new_exp)
        db.commit()
        return new_exp
