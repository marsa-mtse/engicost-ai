import json
import re
from typing import Dict, Any, List
import os
import urllib.parse
from openai import OpenAI
from ai_engine.cost_engine import get_cost_engine

# ─── Project Type Intelligence ────────────────────────────────────────────────
PROJECT_TYPE_HINTS = {
    "villa": {
        "ar": "فيلا سكنية",
        "rooms": ["مدخل رئيسي", "صالة معيشة", "صالة طعام", "مطبخ", "غرفة نوم رئيسية", "حمام"],
        "style_note": "Connected interior spaces with garden and driveway access."
    },
    "apartment": {
        "ar": "شقة سكنية",
        "rooms": ["ردهة", "صالة", "مطبخ مفتوح", "غرفة نوم"],
        "style_note": "Compact layout, all rooms accessible from a central corridor."
    },
    "warehouse": {
        "ar": "مستودع",
        "rooms": ["مبنى رئيسي مفتوح", "مكتب إداري", "حمامات", "غرفة كهرباء"],
        "style_note": "Large open span, high clearance, wide loading doors."
    },
    "mosque": {
        "ar": "مسجد",
        "rooms": ["صحن", "حرم الصلاة للرجال", "حرم الصلاة للنساء", "وضوء رجال", "وضوء نساء", "مكتب الإمام"],
        "style_note": "Qibla wall facing Mecca, ablution areas near entrance, dome over prayer hall."
    },
    "steel": {
        "ar": "هيكل معدني",
        "rooms": ["بلاطة إنشائية", "مخزن", "غرفة تحكم"],
        "style_note": "Steel portal frame structure, IPE columns and beams on regular grid."
    },
    "office": {
        "ar": "مبنى إداري",
        "rooms": ["ردهة استقبال", "مكاتب مفتوحة", "قاعة اجتماعات", "مكتب مدير", "حمامات"],
        "style_note": "Open plan office, glass partitions, central corridor."
    }
}

def detect_project_type(prompt: str, specialty: str) -> str:
    """Detect project type from user prompt and specialty."""
    prompt_lower = prompt.lower()
    if "معدن" in specialty or "steel" in specialty.lower() or "metal" in specialty.lower():
        return "steel"
    if any(w in prompt_lower for w in ["فيلا", "villa", "منزل", "بيت", "house"]):
        return "villa"
    if any(w in prompt_lower for w in ["شقة", "apartment", "flat"]):
        return "apartment"
    if any(w in prompt_lower for w in ["مستودع", "مخزن", "warehouse", "factory", "مصنع"]):
        return "warehouse"
    if any(w in prompt_lower for w in ["مسجد", "mosque", "جامع"]):
        return "mosque"
    if any(w in prompt_lower for w in ["مكتب", "office", "إداري", "admin"]):
        return "office"
    return "villa"  # Default


def smart_parse(data: Any) -> Dict[str, list]:
    """Parse AI output (new room-based schema + legacy wall schema) into standardized format."""
    walls, openings, furniture, labels, rooms = [], [], [], [], []

    # Handle string inputs (extract JSON)
    if isinstance(data, str):
        try:
            match = re.search(r'(\{.*\}|\[.*\])', data, re.DOTALL)
            if match:
                data = json.loads(match.group(1))
            else:
                return {"walls": [], "openings": [], "furniture": [], "labels": [], "rooms": [], "project_info": {}}
        except Exception:
            return {"walls": [], "openings": [], "furniture": [], "labels": [], "rooms": [], "project_info": {}}

    project_info = {}

    if isinstance(data, dict):
        project_info = {
            "title": data.get("project_title", data.get("title", "")),
            "style": data.get("style", ""),
            "total_area": data.get("total_area_m2", 0),
            "floors": data.get("floors", 1),
            "project_type": data.get("project_type", ""),
        }

        # ── NEW SCHEMA: rooms list ──────────────────────────────────
        if "rooms" in data and isinstance(data["rooms"], list):
            rooms = data["rooms"]
            # Convert rooms to walls + labels for legacy rendering
            for room in rooms:
                rx = float(room.get("x_m", room.get("x", 0))) * 100
                ry = float(room.get("y_m", room.get("y", 0))) * 100
                rw = float(room.get("width_m", room.get("w", 4))) * 100
                rh = float(room.get("height_m", room.get("h", 4))) * 100
                rname = room.get("name", "Room")
                rtype = room.get("type", "room").lower()
                wall_thick = 20  # 20cm walls

                # Room boundary walls
                walls.extend([
                    {"x": rx, "y": ry, "w": rw, "h": wall_thick, "is_exterior": room.get("walls", {}).get("south") == "exterior", "room": rname},
                    {"x": rx, "y": ry + rh - wall_thick, "w": rw, "h": wall_thick, "is_exterior": room.get("walls", {}).get("north") == "exterior", "room": rname},
                    {"x": rx, "y": ry, "w": wall_thick, "h": rh, "is_exterior": room.get("walls", {}).get("west") == "exterior", "room": rname},
                    {"x": rx + rw - wall_thick, "y": ry, "w": wall_thick, "h": rh, "is_exterior": room.get("walls", {}).get("east") == "exterior", "room": rname},
                ])

                # Doors in this room
                for door in room.get("doors", []):
                    d_wall = door.get("wall", "south")
                    d_pos = float(door.get("position", 0.5))
                    d_w = float(door.get("width_m", 1.0)) * 100
                    if d_wall in ["south", "north"]:
                        dy = ry if d_wall == "south" else ry + rh - wall_thick
                        openings.append({"name": "Door", "type": "door", "x": rx + (rw * d_pos) - d_w/2, "y": dy, "w": d_w, "h": wall_thick, "swing": door.get("swing", 90)})
                    else:
                        dx = rx if d_wall == "west" else rx + rw - wall_thick
                        openings.append({"name": "Door", "type": "door", "x": dx, "y": ry + (rh * d_pos) - d_w/2, "w": wall_thick, "h": d_w, "swing": door.get("swing", 90)})

                # Windows in this room
                for win in room.get("windows", []):
                    w_wall = win.get("wall", "north")
                    w_pos = float(win.get("position", 0.5))
                    w_w = float(win.get("width_m", 1.2)) * 100
                    if w_wall in ["south", "north"]:
                        wy = ry if w_wall == "south" else ry + rh - wall_thick
                        openings.append({"name": "Window", "type": "window", "x": rx + (rw * w_pos) - w_w/2, "y": wy, "w": w_w, "h": wall_thick})
                    else:
                        wx = rx if w_wall == "west" else rx + rw - wall_thick
                        openings.append({"name": "Window", "type": "window", "x": wx, "y": ry + (rh * w_pos) - w_w/2, "w": wall_thick, "h": w_w})

                # Room label at center
                labels.append({"text": rname, "x": rx + rw/2, "y": ry + rh/2, "area_m2": round((rw/100)*(rh/100), 1)})

                # Room-specific furniture
                if rtype in ["kitchen", "مطبخ"]:
                    furniture.append({"name": "Kitchen Counter", "type": "kitchen", "x": rx + wall_thick, "y": ry + wall_thick, "w": rw - wall_thick*2, "h": 60})
                elif "bed" in rtype or "نوم" in rtype:
                    furniture.append({"name": "Bed", "type": "bed", "x": rx + wall_thick + 20, "y": ry + wall_thick + 20, "w": 160, "h": 200})

        # ── LEGACY SCHEMA: direct walls/openings/furniture ──────────
        else:
            for k in ["walls", "openings", "furniture", "labels"]:
                if k in data and isinstance(data[k], list):
                    if k == "walls": walls.extend(data[k])
                    elif k == "openings": openings.extend(data[k])
                    elif k == "furniture": furniture.extend(data[k])
                    elif k == "labels": labels.extend(data[k])

        # Special elements (pool, greenery, steel grid)
        for item in data.get("special_elements", []):
            furniture.append(item)

    # Handle pool / greenery from furniture list
    for f in data.get("furniture", []) if isinstance(data, dict) else []:
        if not any(x.get("name") == f.get("name") for x in furniture):
            furniture.append(f)

    return {
        "walls": walls,
        "openings": openings,
        "furniture": furniture,
        "labels": labels,
        "rooms": rooms,
        "project_info": project_info
    }


def generate_layout_from_prompt(
    prompt: str,
    specialty: str,
    style_3d: str,
    bed_count: int,
    bath_count: int,
    balcony_count: int,
    floor_count: int,
    landscaping: bool,
    pool_opt: bool,
    creative_mode: bool
) -> tuple[Dict[str, list], str, bool]:
    """
    Calls the AI engine with a highly detailed architectural/engineering prompt.
    Returns parsed rooms data, raw response, and fallback flag.
    """
    engine = get_cost_engine()
    proj_type = detect_project_type(prompt, specialty)
    proj_hints = PROJECT_TYPE_HINTS.get(proj_type, PROJECT_TYPE_HINTS["villa"])

    creative_instruction = ""
    if creative_mode:
        creative_instruction = "Be visionary and innovative — use organic shapes, curved corridors, double-height spaces, and avant-garde spatial arrangements."

    is_steel = proj_type == "steel"
    steel_note = ""
    if is_steel:
        steel_note = """
STEEL STRUCTURE RULES:
- Use a structural grid of 6m x 6m bays minimum
- Include: portal frames, IPE columns, purlins, and bracing
- Mark all rooms as structural spans (no load-bearing internal walls)
- Add "steel_grid_spacing_m" field to each room
"""

    ai_prompt = f"""You are a Senior Licensed Architect and Structural Engineer with 20 years of experience.

PROJECT BRIEF:
- Project Type: {proj_hints["ar"]} ({proj_type})
- Specialty: {specialty}
- Style/Finishes: {style_3d}
- Floors: {floor_count}
- Bedrooms: {bed_count}
- Bathrooms: {bath_count}
- Balconies: {balcony_count}
- Pool: {"YES - design the pool with realistic dimensions" if pool_opt else "No"}
- Landscaping: {"YES - include garden, driveway, trees" if landscaping else "Minimal"}
- Style Notes: {proj_hints["style_note"]}
- Expected Key Rooms (mandatory): {", ".join(proj_hints["rooms"])}
- Engineer's Specific Request: {prompt if prompt else "Standard layout"}
{steel_note}
{creative_instruction}

CRITICAL RULES:
1. ALL coordinates and dimensions MUST BE IN METERS (not cm, not pixels).
2. Minimum room size: 10 m² (no tiny rooms).
3. Rooms must NOT overlap — ensure proper adjacency.
4. Exterior walls should form a coherent building footprint.
5. Every room MUST have at least 1 door. Main rooms must have windows.
6. The total building footprint should be realistic for the project type.

Return ONLY a valid JSON object (no markdown, no explanation) with this EXACT structure:
{{
  "project_title": "Project Name",
  "project_type": "{proj_type}",
  "style": "{style_3d}",
  "floors": {floor_count},
  "total_area_m2": <realistic_number>,
  "rooms": [
    {{
      "name": "Room Name in Arabic and English",
      "type": "living|bedroom|bathroom|kitchen|corridor|garage|pool|garden|office|hall|steel_bay",
      "x_m": <x_origin_in_meters>,
      "y_m": <y_origin_in_meters>,
      "width_m": <width_in_meters>,
      "height_m": <depth_in_meters>,
      "walls": {{
        "north": "exterior|interior|shared",
        "south": "exterior|interior|shared",
        "east": "exterior|interior|shared",
        "west": "exterior|interior|shared"
      }},
      "doors": [
        {{"wall": "south|north|east|west", "position": 0.5, "width_m": 1.0, "swing": 90}}
      ],
      "windows": [
        {{"wall": "north|east", "position": 0.3, "width_m": 1.5}}
      ],
      "finish_floor": "Marble|Tile|Wood|Concrete|Steel Grating",
      "finish_walls": "Paint|Wallpaper|Stone|Glass|Metal cladding",
      "ceiling_height_m": 3.0
    }}
  ],
  "special_elements": [
    {{"name": "Swimming Pool", "type": "pool", "x": 20, "y": -5, "w": 10, "h": 5}},
    {{"name": "Garden", "type": "greenery", "x": -8, "y": 0, "w": 7, "h": 15}}
  ]
}}

GENERATE AT LEAST {max(bed_count + bath_count + 4, 8)} ROOMS. Make it architecturally coherent and realistic.
"""

    # 1. Try Groq
    res, err = engine._call_groq(ai_prompt, expect_json=True)
    raw_response = str(res)
    fallback_used = False

    # 2. Fallback to Gemini
    if not res or (isinstance(res, dict) and "error" in res) or (isinstance(res, str) and len(res) < 100):
        res, err = engine._call_gemini_text(ai_prompt, expect_json=True)
        fallback_used = True
        raw_response = str(res)

    parsed = smart_parse(res)

    # Validate: need at least 3 walls to be useful
    if len(parsed.get("walls", [])) < 3 and len(parsed.get("rooms", [])) < 2:
        parsed["walls"] = []  # Force algorithmic fallback in the view

    return parsed, raw_response, fallback_used

def analyze_plan_image(image_bytes: bytes, file_extension: str = "png") -> Dict[str, Any]:
    """
    Analyze an uploaded architectural floor plan image using Gemini Vision.
    Returns structured rooms data in the standard JSON format.
    """
    import base64
    engine = get_cost_engine()

    # Encode image to base64
    b64_image = base64.b64encode(image_bytes).decode("utf-8")
    mime_type = f"image/{file_extension.lower().replace('jpg', 'jpeg')}"

    vision_prompt = """You are an expert architectural engineer and CAD analyst.
Analyze this floor plan image and extract ALL rooms visible in it.

Return ONLY a valid JSON object (no markdown, no explanation) with this EXACT structure:
{
  "project_title": "Extracted Plan",
  "project_type": "villa",
  "style": "Modern",
  "floors": 1,
  "total_area_m2": <estimated_area>,
  "rooms": [
    {
      "name": "Room name in Arabic (English)",
      "type": "living|bedroom|bathroom|kitchen|corridor|garage|hall|office",
      "x_m": <x_origin_in_meters>,
      "y_m": <y_origin_in_meters>,
      "width_m": <width_in_meters>,
      "height_m": <depth_in_meters>,
      "walls": {"north": "exterior|interior", "south": "exterior|interior", "east": "exterior|interior", "west": "exterior|interior"},
      "doors": [{"wall": "south|north|east|west", "position": 0.5, "width_m": 1.0, "swing": 90}],
      "windows": [{"wall": "north", "position": 0.5, "width_m": 1.2}],
      "finish_floor": "Tile|Marble|Wood",
      "ceiling_height_m": 3.0
    }
  ],
  "special_elements": []
}

CRITICAL RULES:
1. Estimate realistic dimensions in METERS from the drawing scale.
2. Do NOT overlap rooms — maintain proper adjacency.
3. Identify at least the main visible rooms.
4. If scale is not clear, assume standard room sizes (bedroom: 4x4m, bathroom: 2x2.5m, living: 5x6m).
"""

    try:
        import google.generativeai as genai
        import os
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            api_key = os.environ.get("GOOGLE_API_KEY", "")
        
        if api_key:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            
            response = model.generate_content([
                vision_prompt,
                {"mime_type": mime_type, "data": b64_image}
            ])
            raw = response.text
            # Parse JSON from response
            match = re.search(r'(\{.*\})', raw, re.DOTALL)
            if match:
                data = json.loads(match.group(1))
                return smart_parse(data)
    except Exception as e:
        print(f"Vision analysis error: {e}")
    
    # Return empty structure on failure
    return {"walls": [], "openings": [], "furniture": [], "labels": [], "rooms": [], 
            "project_info": {"title": "Uploaded Plan", "error": "Could not parse image"}}


def extract_quantities_from_plan(rooms_data: dict, specialty: str = "معماري") -> str:\n    \"\"\"\n    Converts AI SVG pixel dimensions into real-world quantities (meters, square meters) \n    for the BOQ Cost Engine.\n    Assuming scale: 100 pixels = 1 meter.\n    \"\"\"\n    SCALE = 0.01 # 100 units = 1 meter\n    CEILING_HEIGHT = 3.0 # meters\n    \n    walls = rooms_data.get("walls", [])\n    openings = rooms_data.get("openings", [])\n    floors = rooms_data.get("floors", 1)\n    \n    # Calculate Plan Bounding Box for Total Area\n    all_x = [w.get("x", 0) for w in walls] + [w.get("x",0) + w.get("w",0) for w in walls]\n    all_y = [w.get("y", 0) for w in walls] + [w.get("y",0) + w.get("h",0) for w in walls]\n    \n    if not all_x or not all_y:\n        return "لم يتم العثور على أبعاد هندسية في المخطط."\n        \n    width_m = (max(all_x) - min(all_x)) * SCALE\n    length_m = (max(all_y) - min(all_y)) * SCALE\n    floor_area_m2 = width_m * length_m\n    total_built_area = floor_area_m2 * floors\n    \n    # Wall Lengths\n    total_wall_length_m = 0\n    for w in walls:\n        length = max(w.get("w", 0), w.get("h", 0)) * SCALE\n        total_wall_length_m += length\n        \n    total_wall_area_m2 = total_wall_length_m * CEILING_HEIGHT * floors\n    \n    # Openings\n    doors_count = sum(1 for o in openings if "door" in str(o.get("type", "")).lower() or "باب" in str(o.get("name", "")))\n    windows_count = sum(1 for o in openings if "win" in str(o.get("type", "")).lower() or "نافذة" in str(o.get("name", "")))\n    \n    # If no doors/windows explicitly found, estimate roughly based on area\n    if doors_count == 0: doors_count = max(1, int(floor_area_m2 / 15)) * floors\n    if windows_count == 0: windows_count = max(2, int(floor_area_m2 / 12)) * floors\n    \n    # Concrete Volumes (Approximate 20cm slab + columns/footings ratio)\n    slab_concrete_m3 = total_built_area * 0.20\n    footing_concrete_m3 = floor_area_m2 * 0.25 # Only for ground floor\n    total_concrete_m3 = slab_concrete_m3 + footing_concrete_m3\n    \n    excavation_m3 = floor_area_m2 * 1.5 # 1.5m depth excavation\n    \n    # Generate formatted BOQ text for AI to price\n    boq_lines = [\n        f"مشروع: {rooms_data.get('project_title', 'مبنى مستخرج من الرسم')} - عدد الأدوار: {floors}",\n        "",\n        "--- الأعمال الترابية والخرسانات ---",\n        f"أعمال الحفر والردم للقواعد: {int(excavation_m3)} متر مكعب",\n        f"خرسانة مسلحة (أسقف وأعمدة وقواعد): {int(total_concrete_m3)} متر مكعب",\n        "",\n        "--- أعمال المباني والمحارة ---",\n        f"بناء جدران (طوب أحمر): {int(total_wall_area_m2)} متر مربع",\n        f"بياض تخشين (محارة) داخلي وخارجي: {int(total_wall_area_m2 * 2)} متر مربع",\n        "",\n        "--- أعمال التشطيبات ---",\n        f"أرضيات سيراميك/بورسلين: {int(total_built_area)} متر مربع",\n        f"أعمال دهانات (بلاستيك): {int(total_wall_area_m2 * 1.8)} متر مربع",\n        "",\n        "--- أعمال النجارة والألوميتال ---",\n        f"توريد وتركيب أبواب خشبية: {doors_count} عدد",\n        f"توريد وتركيب نوافذ ألوميتال: {windows_count} عدد",\n    ]\n    \n    # Add special elements\n    furnitures = rooms_data.get("furniture", [])\n    bathrooms = sum(1 for l in rooms_data.get("labels", []) if "bath" in str(l.get("text","")).lower() or "حمام" in str(l.get("text","")))\n    if bathrooms == 0: bathrooms = floors * 2 # Fallback\n    \n    boq_lines.append("")\n    boq_lines.append("--- الأعمال الصحية والكهربائية ---")\n    boq_lines.append(f"تأسيس وتشطيب حمامات كاملة: {bathrooms} عدد")\n    boq_lines.append(f"تأسيس كهرباء (نقاط ومخارج): {int(total_built_area * 0.8)} نقطة")\n    \n    has_pool = any("pool" in str(f.get("type","")).lower() for f in furnitures)\n    if has_pool:\n        boq_lines.append("")\n        boq_lines.append("--- أعمال خارجية وتنسيق موقع ---")\n        boq_lines.append("إنشاء وتأسيس حمام سباحة خاص: 1 مقطوعية")\n        \n    has_garden = any("green" in str(f.get("type","")).lower() or "land" in str(f.get("type","")).lower() for f in furnitures)\n    if has_garden:\n        boq_lines.append(f"أعمال لاندسكيب ومساحات خضراء: {int(floor_area_m2 * 0.3)} متر مربع")\n\n    return "\\n".join(boq_lines)\n\n\ndef generate_3d_render(prompt: str, style: str, view_type: str, specialty: str) -> str:
    """Generate professional 3D architectural renders using DALL-E 3 or fallback."""
    api_key = os.environ.get("OPENAI_API_KEY", "")
    
    # Detailed architectural prompt engineering
    base_prompt = f"Professional 8k hyper-realistic architectural concept design, {style} {specialty}. "
    if view_type == "Isometric":
        base_prompt += "3D Isometric cutaway floor plan perspective, showing interior layout explicitly from a high angle, highly detailed architectural model. "
    elif view_type == "Perspective":
        base_prompt += "Exterior perspective shot, photorealistic, cinematic lighting, Unreal Engine 5 aesthetic, V-Ray render. "
    else:
        base_prompt += "Interior design render, highly detailed, realistic materials and lighting, modern elegant aesthetic. "
        
    if prompt:
        base_prompt += f"Specific details requested: {prompt}"

    # Try DALL-E 3 if API key available
    if api_key and api_key.startswith("sk-"):
        try:
            client = OpenAI(api_key=api_key)
            response = client.images.generate(
                model="dall-e-3",
                prompt=base_prompt[:1000], # max length
                size="1024x1024",
                quality="hd",
                n=1,
            )
            return response.data[0].url
        except Exception as e:
            print(f"DALL-E 3 API Error: {e}")
            pass # Fallback to pollinations smoothly

    # Fallback to Pollinations.ai
    encoded_prompt = urllib.parse.quote(base_prompt)
    import time
    timestamp = int(time.time())
    img_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1920&height=1080&nologo=true&seed={timestamp}"
    return img_url

