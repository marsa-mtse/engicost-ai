from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from services.structural_service import StructuralService
from services.cost_service import CostService
from services.inventory_service import InventoryService
from services.finance_service import FinanceService
from ai_engine.cost_engine import get_cost_engine
from ai_engine.market_api import MarketEngine
from database import SessionLocal
from typing import Optional, List, Dict

app = FastAPI(
    title="EngiCost AI API",
    description="Enterprise-grade Engineering Services for Construction Estimation & Design",
    version="1.0.0"
)

# ─── Pydantic Models ──────────────────────────────────────────────────────────

class ColumnRequest(BaseModel):
    b_mm: float
    t_mm: float
    height_m: float
    fcu_mpa: float
    fy_mpa: float
    load_kn: float
    rho_pct: float

class BeamRequest(BaseModel):
    b_mm: float
    h_mm: float
    span_m: float
    fcu_mpa: float
    fy_mpa: float
    moment_knm: float

class SlabRequest(BaseModel):
    span_m: float
    thickness_mm: float
    fcu_mpa: float
    fy_mpa: float
    load_kpa: float
    slab_type: str = "one-way"

class FootingRequest(BaseModel):
    load_kn: float
    qa_kpa: float
    fcu_mpa: float
    fy_mpa: float
    col_b_mm: float
    col_d_mm: float

class TenderRequest(BaseModel):
    direct_costs: float
    overhead_pct: float
    contingency_pct: float
    profit_pct: float
    vat_pct: float

class BOQMatchRequest(BaseModel):
    items: List[Dict]
    currency: str = "USD"
    rate: float = 1.0

class PurchaseRequest(BaseModel):
    project_id: int
    name: str
    unit: str
    qty: float
    price: float
    note: str = ""

class IssueRequest(BaseModel):
    item_id: int
    qty: float
    note: str = ""

class ExpenseRequest(BaseModel):
    project_id: int
    category: str
    amount: float
    description: str = ""

# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/")
def read_root():
    return {"message": "Welcome to EngiCost AI API Suite", "status": "online"}

@app.post("/structural/column")
def design_column(req: ColumnRequest):
    try:
        return StructuralService.calc_column(
            req.b_mm, req.t_mm, req.height_m, req.fcu_mpa, req.fy_mpa, req.load_kn, req.rho_pct
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/structural/beam")
def design_beam(req: BeamRequest):
    try:
        return StructuralService.calc_beam(
            req.b_mm, req.h_mm, req.span_m, req.fcu_mpa, req.fy_mpa, req.moment_knm
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/structural/slab")
def design_slab(req: SlabRequest):
    try:
        return StructuralService.calc_slab(
            req.span_m, req.thickness_mm, req.fcu_mpa, req.fy_mpa, req.load_kpa, req.slab_type
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/structural/footing")
def design_footing(req: FootingRequest):
    try:
        return StructuralService.calc_footing(
            req.load_kn, req.qa_kpa, req.fcu_mpa, req.fy_mpa, req.col_b_mm, req.col_d_mm
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ─── Cost Endpoints ───────────────────────────────────────────────────────────

@app.post("/cost/calculate-tender")
def calculate_tender(req: TenderRequest):
    try:
        return CostService.calculate_tender_price(
            req.direct_costs, req.overhead_pct, req.contingency_pct, req.profit_pct, req.vat_pct
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/cost/match-boq")
def match_boq(req: BOQMatchRequest):
    try:
        engine = get_cost_engine()
        market_data = MarketEngine.get_live_prices()
        prices = market_data.get('prices', {})
        
        return CostService.match_boq_items(
            engine, req.items, prices, req.currency, req.rate
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ─── Inventory Endpoints ──────────────────────────────────────────────────────

@app.get("/inventory/stock/{project_id}")
def get_stock(project_id: int):
    db = SessionLocal()
    try:
        return InventoryService.get_stock_status(db, project_id)
    finally:
        db.close()

@app.post("/inventory/purchase")
def log_purchase(req: PurchaseRequest):
    db = SessionLocal()
    try:
        return InventoryService.log_purchase(
            db, req.project_id, req.name, req.unit, req.qty, req.price, req.note
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()

# ─── Finance Endpoints ────────────────────────────────────────────────────────

@app.get("/finance/analysis/{project_id}")
def get_finances(project_id: int):
    db = SessionLocal()
    try:
        return FinanceService.get_project_financials(db, project_id)
    finally:
        db.close()

@app.post("/finance/expense")
def log_expense(req: ExpenseRequest):
    db = SessionLocal()
    try:
        return FinanceService.log_expense(
            db, req.project_id, req.category, req.amount, req.description
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
