import ezdxf
import io
from typing import Dict, Any

def generate_dxf_from_json(plan_data: Dict[str, Any]) -> bytes:
    """
    Generates a professional AutoCAD-compatible DXF file (v2010),
    including properly scaled layers and linear dimensions.
    """
    doc = ezdxf.new(dxfversion='R2010')
    msp = doc.modelspace()
    
    # ─── SETUP LAYERS ──────────────────────────────
    doc.layers.add("WALLS", color=ezdxf.colors.CYAN)
    doc.layers.add("OPENINGS", color=ezdxf.colors.YELLOW)
    doc.layers.add("FURNITURE", color=ezdxf.colors.GREEN)
    doc.layers.add("LABELS", color=ezdxf.colors.WHITE)
    doc.layers.add("DIMENSIONS", color=ezdxf.colors.MAGENTA)
    doc.layers.add("STEEL_GRID", color=ezdxf.colors.RED, linetype="DASHDOT")

    # Set up dimension style
    dimstyle = doc.dimstyles.new("ARCH_METRIC")
    dimstyle.dxf.dimtxt = 15      # Text height
    dimstyle.dxf.dimclrt = ezdxf.colors.WHITE  # Text color
    dimstyle.dxf.dimclrd = ezdxf.colors.MAGENTA # Dim line color
    dimstyle.dxf.dimclre = ezdxf.colors.MAGENTA # Ext line color
    dimstyle.dxf.dimdec = 1       # 1 decimal place

    def add_dimension(p1, p2, offset=50, angle=0):
        """Helper to add linear dimensions."""
        dim = msp.add_linear_dim(
            base=(p1[0], p1[1] + offset) if angle == 0 else (p1[0] - offset, p1[1]),
            p1=p1,
            p2=p2,
            angle=angle,
            dxfattribs={'layer': 'DIMENSIONS'}
        )
        dim.render()

    walls = plan_data.get('walls', [])
    if walls:
        min_x = min([w.get('x',0) for w in walls])
        max_x = max([w.get('x',0)+w.get('w',0) for w in walls])
        min_y = min([w.get('y',0) for w in walls])
        max_y = max([w.get('y',0)+w.get('h',0) for w in walls])
        
        # Overall outer dimensions
        add_dimension((min_x, max_y), (max_x, max_y), offset=100, angle=0)  # Top Width
        add_dimension((min_x, min_y), (min_x, max_y), offset=100, angle=90) # Left Height

    # ─── DRAW WALLS ──────────────────────────────
    for wall in walls:
        x, y = wall.get('x', 0), wall.get('y', 0)
        w, h = max(wall.get('w', 10), 10), max(wall.get('h', 10), 10)
        
        msp.add_lwpolyline(
            [(x, y), (x + w, y), (x + w, y + h), (x, y + h)], 
            close=True, dxfattribs={'layer': 'WALLS'}
        )

    # ─── DRAW OPENINGS ────────────────────────
    for opening in plan_data.get('openings', []):
        x, y = opening.get('x', 0), opening.get('y', 0)
        w, h = max(opening.get('w', 20), 10), max(opening.get('h', 20), 10)
        
        otype = str(opening.get('type', '')).lower()
        if 'door' in otype:
            # Door Arc
            if h > w: # Vertical door
                msp.add_line((x, y), (x+w, y), dxfattribs={'layer': 'OPENINGS'})
                msp.add_arc((x, y), radius=w, start_angle=0, end_angle=90, dxfattribs={'layer': 'OPENINGS'})
            else: # Horizontal door
                msp.add_line((x, y), (x, y+h), dxfattribs={'layer': 'OPENINGS'})
                msp.add_arc((x, y), radius=h, start_angle=270, end_angle=360, dxfattribs={'layer': 'OPENINGS'})
        else:
            # Window
            msp.add_lwpolyline([(x, y), (x+w, y), (x+w, y+h), (x, y+h)], close=True, dxfattribs={'layer': 'OPENINGS'})
            if w > h:
                msp.add_line((x, y+h/2), (x+w, y+h/2), dxfattribs={'layer': 'OPENINGS'})
            else:
                msp.add_line((x+w/2, y), (x+w/2, y+h), dxfattribs={'layer': 'OPENINGS'})

    # ─── FURNITURE & LANDSCAPE ────────────────
    for furn in plan_data.get('furniture', []):
        x, y = furn.get('x', 0), furn.get('y', 0)
        w, h = max(furn.get('w', 50), 20), max(furn.get('h', 50), 20)
        ftype = str(furn.get('type', '')).lower()
        
        if 'tree' in ftype or 'green' in ftype:
            r = min(w, h)/2
            msp.add_circle((x+w/2, y+h/2), radius=r, dxfattribs={'layer': 'FURNITURE'})
            # Add cross inside tree
            msp.add_line((x+w/2, y), (x+w/2, y+h), dxfattribs={'layer': 'FURNITURE'})
            msp.add_line((x, y+h/2), (x+w, y+h/2), dxfattribs={'layer': 'FURNITURE'})
        else:
            msp.add_lwpolyline([(x, y), (x+w, y), (x+w, y+h), (x, y+h)], close=True, dxfattribs={'layer': 'FURNITURE'})
        
        name = furn.get('name', '')
        if name:
            txt = msp.add_text(name, dxfattribs={'layer': 'FURNITURE'})
            txt.set_placement((x+w/2, y+h/2), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
            txt.dxf.height = max(8, min(w, h) / 5)

    # ─── STEEL GRID (if applicable) ───────────
    if plan_data.get("project_info", {}).get("project_type") == "steel":
        # Draw IPE Columns at intersections
        for wall in walls:
            x, y = wall.get('x', 0), wall.get('y', 0)
            msp.add_lwpolyline([(x-10, y-10), (x+10, y-10), (x+10, y+10), (x-10, y+10)], close=True, dxfattribs={'layer': 'STEEL_GRID', 'color': ezdxf.colors.RED})
            msp.add_circle((x, y), radius=15, dxfattribs={'layer': 'STEEL_GRID'})

    # ─── ROOM LABELS ─────────────────────────
    for lbl in plan_data.get('labels', []):
        x, y = lbl.get('x', 0), lbl.get('y', 0)
        txt_str = lbl.get('text', 'Room')
        area = lbl.get('area_m2', '')
        
        txt = msp.add_text(txt_str, dxfattribs={'layer': 'LABELS', 'color': ezdxf.colors.WHITE})
        txt.set_placement((x, y), align=ezdxf.enums.TextEntityAlignment.BOTTOM_CENTER)
        txt.dxf.height = 20
        
        if area:
            txt_area = msp.add_text(f"{area} m2", dxfattribs={'layer': 'LABELS', 'color': ezdxf.colors.CYAN})
            txt_area.set_placement((x, y - 25), align=ezdxf.enums.TextEntityAlignment.TOP_CENTER)
            txt_area.dxf.height = 14

    out_stream = io.StringIO()
    doc.write(out_stream)
    return out_stream.getvalue().encode('utf-8')
