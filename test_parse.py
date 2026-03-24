import sys
import json
import re

sys.path.append('.')
from ai_engine.cost_engine import get_cost_engine

engine = get_cost_engine()
ai_prompt = """You are a Senior Architect. Design a Modern (Gray/Glass) style project.
Generate a highly detailed architectural layout for a Architectural project.

STRICT REQUIREMENTS:
- Bedrooms: 5
- Bathrooms: 4
- Balconies: 1
- Style: Modern (Gray/Glass)

Return ONLY a JSON object. Coordinates in cm.
{
    "project_title": "Custom Modern Design",
    "walls": [{"name": "External Wall", "x": 0, "y": 0, "w": 20, "h": 1000}],
    "labels": [{"text": "Master Bedroom", "x": 200, "y": 200}]
}"""

res, err = engine._call_groq(ai_prompt, expect_json=True)
print('Groq Result:', repr(res)[:200] if res else repr(res))
print('Groq Error:', repr(err))

def smart_parse(data):
    walls, openings, furniture, labels = [], [], [], []
    if isinstance(data, str):
        try:
            match = re.search(r'(\{.*\}|\[.*\])', data, re.DOTALL)
            if match:
                data = json.loads(match.group(1))
            else:
                return {'walls': []}
        except:
            return {'walls': []}

    targets = []
    if isinstance(data, list): targets = data
    elif isinstance(data, dict):
        for k in ['walls', 'openings', 'furniture', 'labels']:
            if k in data and isinstance(data[k], list):
                if k == 'walls': walls.extend(data[k])
                elif k == 'labels': labels.extend(data[k])
        for k, v in data.items():
            if k not in ['walls', 'openings', 'furniture', 'labels'] and isinstance(v, list):
                targets.extend(v)

    for item in targets:
        if not isinstance(item, dict): continue
        itype = str(item.get('type', item.get('category', 'furniture'))).lower()
        if 'wall' in itype: walls.append(item)

    return {'walls': walls}

parsed = smart_parse(res)
print('Parsed Walls length:', len(parsed['walls']))
