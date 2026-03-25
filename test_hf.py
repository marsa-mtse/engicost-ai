import os
token = os.environ.get("HF_TOKEN", "MISSING")
print(f"HF_TOKEN: {token[:4]}***" if token != "MISSING" else "HF_TOKEN: MISSING")
