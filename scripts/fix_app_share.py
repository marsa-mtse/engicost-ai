import os

def apply_fix():
    file_path = r'd:\engicost-ai\app.py'
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()

    target = """    if not st.session_state.authenticated:
        from views import auth_view
        auth_view.render_login_signup()
    else:
        render_app()"""

    replacement = """    if "share" in st.query_params:
        from views import shared_project_view
        shared_project_view.render_shared_project(st.query_params["share"])
    elif not st.session_state.authenticated:
        from views import auth_view
        auth_view.render_login_signup()
    else:
        render_app()"""

    if target in text:
        new_text = text.replace(target, replacement)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_text)
        print("SUCCESS APP.PY SHARE")
    else:
        print("TARGET NOT FOUND IN APP.PY")

if __name__ == '__main__':
    apply_fix()
