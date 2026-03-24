import ezdxf
import io

def generate_dxf_from_json(rooms_data: dict) -> bytes:
    """
    Converts the AI JSON layout into an AutoCAD-compatible DXF file.
    """
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    
    # Create layers
    doc.layers.add("WALLS", color=2) # Yellow
    doc.layers.add("FURNITURE", color=3) # Green
    doc.layers.add("LABELS", color=7) # White/Black
    
    # Draw walls as polylines or individual lines
    for wall in rooms_data.get("walls", []):
        x, y, w, h = wall.get("x", 0), wall.get("y", 0), wall.get("w", 0), wall.get("h", 0)
        # AutoCAD uses bottom-left origin, while SVG uses top-left. We flip Y axis dynamically.
        y_auto = -y  # Simple flip for visualization
        
        # Add 4 lines to make the wall rectangle
        p1 = (x, y_auto)
        p2 = (x + w, y_auto)
        p3 = (x + w, y_auto - h)
        p4 = (x, y_auto - h)
        
        msp.add_line(p1, p2, dxfattribs={'layer': 'WALLS'})
        msp.add_line(p2, p3, dxfattribs={'layer': 'WALLS'})
        msp.add_line(p3, p4, dxfattribs={'layer': 'WALLS'})
        msp.add_line(p4, p1, dxfattribs={'layer': 'WALLS'})

    # Draw furniture as simple boxes
    for furn in rooms_data.get("furniture", []):
        x, y, w, h = furn.get("x", 0), furn.get("y", 0), furn.get("w", 0), furn.get("h", 0)
        y_auto = -y
        p1, p2, p3, p4 = (x, y_auto), (x + w, y_auto), (x + w, y_auto - h), (x, y_auto - h)
        
        msp.add_line(p1, p2, dxfattribs={'layer': 'FURNITURE'})
        msp.add_line(p2, p3, dxfattribs={'layer': 'FURNITURE'})
        msp.add_line(p3, p4, dxfattribs={'layer': 'FURNITURE'})
        msp.add_line(p4, p1, dxfattribs={'layer': 'FURNITURE'})
        
        # Add a text label in the center of the furniture
        text_name = furn.get("name", "Item")
        msp.add_text(text_name, dxfattribs={
            'layer': 'FURNITURE',
            'height': 15.0
        }).set_placement((x + w/2, y_auto - h/2), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)

    # Draw labels (Rooms)
    for label in rooms_data.get("labels", []):
        x, y = label.get("x", 0), label.get("y", 0)
        y_auto = -y
        text = label.get("text", "Room")
        
        msp.add_text(text, dxfattribs={
            'layer': 'LABELS',
            'height': 30.0 # Make room names larger
        }).set_placement((x, y_auto), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)

    # Export to memory buffer
    stream = io.StringIO()
    doc.write(stream)
    
    # Convert StringIO to bytes for downloading in Streamlit
    bytes_data = stream.getvalue().encode('utf-8')
    stream.close()
    
    return bytes_data
