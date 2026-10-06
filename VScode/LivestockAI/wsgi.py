import os
from app import app

__all__ = ["app"]

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    host = os.getenv("HOST", "0.0.0.0")
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    
    print("\n" + "=" * 60)
    print(" LivestockAI Server Starting...")
    print(f" -> Local Web:    http://127.0.0.1:{port}/")
    print(f" -> Android API:  http://10.0.2.2:{port}/api/v1/ (Emulator)")
    print(f" -> Network API:  http://0.0.0.0:{port}/api/v1/")
    print("=" * 60 + "\n")
    
    app.run(host=host, port=port, debug=debug)