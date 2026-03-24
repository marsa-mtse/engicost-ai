import traceback
try:
    import app
    print("app imported successfully")
except Exception as e:
    traceback.print_exc()
