import os
import json
import base64

def get_file_content(path):
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def build():
    root = "."
    # Use explicit filenames to avoid missing files
    base_files = ["app.py", "auth.py", "database.py", "utils.py", "config.py", "sync_engine.py"]
    files = {}
    for bf in base_files:
        if os.path.exists(bf):
            files[bf] = get_file_content(bf)
    
    # Views
    if os.path.exists("views"):
        for f in os.listdir("views"):
            if f.endswith(".py"):
                files[f"views/{f}"] = get_file_content(f"views/{f}")
                
    # AI Engine
    if os.path.exists("ai_engine"):
        for f in os.listdir("ai_engine"):
            if f.endswith(".py"):
                files[f"ai_engine/{f}"] = get_file_content(f"ai_engine/{f}")
                
    # Read local stlite components
    stlite_css_path = "static/stlite.css"
    stlite_js_path = "static/stlite.js"
    
    if not os.path.exists(stlite_css_path) or not os.path.exists(stlite_js_path):
        print("Error: static/stlite.css or static/stlite.js not found. Please download them first.")
        return

    stlite_css = get_file_content(stlite_css_path)
    stlite_js = get_file_content(stlite_js_path)

    # Generate stlite HTML
    # We use place holders and .replace() to avoid f-string escaping issues with JS/CSS
    html_template = """
<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge" />
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no" />
    <title>EngiCost AI - Site Edition (100% Offline)</title>
    <style>STLITE_CSS_CONTENT</style>
  </head>
  <body>
    <div id="root"></div>
    <script>STLITE_JS_CONTENT</script>
    <script>
      stlite.mount({
        requirements: ["plotly", "pandas", "sqlalchemy", "bcrypt-py"],
        files: FILES_JSON_PLACEHOLDER,
        entrypoint: "app.py",
      }, document.getElementById("root"));
    </script>
  </body>
</html>
"""
    
    files_json = json.dumps(files)
    final_html = html_template.replace("FILES_JSON_PLACEHOLDER", files_json)
    final_html = final_html.replace("STLITE_CSS_CONTENT", stlite_css)
    final_html = final_html.replace("STLITE_JS_CONTENT", stlite_js)
    
    with open("engicost_site_edition.html", "w", encoding="utf-8") as f:
        f.write(final_html)
    
    print("Successfully generated engicost_site_edition.html (Standalone Edition)")

if __name__ == "__main__":
    build()
