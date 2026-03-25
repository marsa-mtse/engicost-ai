import datetime
from typing import List, Dict, Any, Optional
from database import InventoryItem, MaterialTransaction, Project

class InventoryService:
    @staticmethod
    def get_stock_status(db, project_id: int) -> List[Dict]:
        items = db.query(InventoryItem).filter(InventoryItem.project_id == project_id).all()
        return [
            {
                "id": item.id,
                "name": item.name,
                "quantity": item.quantity,
                "unit": item.unit,
                "avg_price": item.avg_price,
                "total_value": item.quantity * item.avg_price,
                "last_updated": item.last_updated
            }
            for item in items
        ]

    @staticmethod
    def log_purchase(db, project_id: int, name: str, unit: str, qty: float, price: float, note: str = ""):
        # Check if item exists
        item = db.query(InventoryItem).filter(
            InventoryItem.project_id == project_id,
            InventoryItem.name == name
        ).first()
        
        if not item:
            item = InventoryItem(
                project_id=project_id,
                name=name,
                unit=unit,
                quantity=0,
                avg_price=0
            )
            db.add(item)
            db.flush()
        
        # Update average price and quantity
        current_total_cost = item.quantity * item.avg_price
        new_total_cost = current_total_cost + (qty * price)
        item.quantity += qty
        item.avg_price = new_total_cost / item.quantity
        item.last_updated = datetime.datetime.utcnow()
        
        # Log transaction
        trans = MaterialTransaction(
            item_id=item.id,
            type="IN",
            quantity=qty,
            unit_price=price,
            note=note
        )
        db.add(trans)
        db.commit()
        return item

    @staticmethod
    def issue_material(db, item_id: int, qty: float, note: str = ""):
        item = db.query(InventoryItem).get(item_id)
        if not item or item.quantity < qty:
            return None, "Insufficient stock or item not found"
        
        item.quantity -= qty
        item.last_updated = datetime.datetime.utcnow()
        
        # Log transaction (issued at average cost)
        trans = MaterialTransaction(
            item_id=item.id,
            type="OUT",
            quantity=qty,
            unit_price=item.avg_price,
            note=note
        )
        db.add(trans)
        db.commit()
        return item, None
