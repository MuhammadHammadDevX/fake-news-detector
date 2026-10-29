# ====================================================================
# Factify AI - Production WSGI Application Entrypoint
# ====================================================================

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5002))
    print("=" * 60)
    print("  🛡️ FACTIFY AI — PRODUCTION WSGI SERVER (Waitress)")
    print(f"  Access URL: http://127.0.0.1:{port}")
    print("=" * 60)
    
    try:
        from waitress import serve
        serve(app, host="0.0.0.0", port=port, threads=8)
    except ImportError:
        print("[WARN] Waitress not installed, falling back to standard server.")
        app.run(host="0.0.0.0", port=port, debug=False)
