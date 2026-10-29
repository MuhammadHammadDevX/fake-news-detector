#!/usr/bin/env python3
"""
Factify AI — Automated Production Build & Release Packager
=========================================================
This script generates a clean, optimized, production-ready release
in the `dist/` directory, including WSGI launchers and a deployment ZIP archive.
"""

import os
import sys
import shutil
import zipfile
import py_compile
from datetime import datetime

# Safe UTF-8 console output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(ROOT_DIR, "dist")
BUILD_DIR = os.path.join(DIST_DIR, "factify-release")
VERSION = "1.0.0"

def log(msg, symbol="👉"):
    print(f"{symbol} {msg}")

def clean_caches(base_dir):
    """Removes __pycache__, .pyc, and temporary scratch files."""
    cleaned = 0
    for root, dirs, files in os.walk(base_dir, topdown=False):
        for d in dirs:
            if d in ("__pycache__", ".pytest_cache", "node_modules"):
                shutil.rmtree(os.path.join(root, d), ignore_errors=True)
                cleaned += 1
        for f in files:
            if f.endswith((".pyc", ".pyo", ".log")) and f != "requirements.txt":
                try:
                    os.remove(os.path.join(root, f))
                    cleaned += 1
                except Exception:
                    pass
    return cleaned

def validate_sources():
    """Validates Python syntax of core backend modules."""
    log("Validating Python source files...", "🔍")
    modules = [
        "backend/app.py",
        "backend/model.py",
        "backend/image_analyzer.py",
        "backend/train.py",
        "backend/setup_admin.py",
        "backend/wsgi.py"
    ]
    for rel_path in modules:
        full_path = os.path.join(ROOT_DIR, rel_path)
        if os.path.exists(full_path):
            try:
                py_compile.compile(full_path, doraise=True)
                log(f"  OK: {rel_path}", "  ✓")
            except py_compile.PyCompileError as e:
                log(f"Syntax error in {rel_path}: {e}", "  ❌")
                sys.exit(1)

def assemble_release():
    """Assembles all production files into dist/factify-release."""
    if os.path.exists(DIST_DIR):
        log("Cleaning previous build directory...", "🧹")
        shutil.rmtree(DIST_DIR, ignore_errors=True)
    
    os.makedirs(BUILD_DIR, exist_ok=True)
    log(f"Assembling production build in {BUILD_DIR}...", "📦")

    # 1. Copy Backend
    backend_dest = os.path.join(BUILD_DIR, "backend")
    shutil.copytree(
        os.path.join(ROOT_DIR, "backend"),
        backend_dest,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".env", "venv", "*.log")
    )
    os.makedirs(os.path.join(backend_dest, "dataset"), exist_ok=True)
    os.makedirs(os.path.join(backend_dest, "temp_uploads"), exist_ok=True)

    # 2. Copy Frontend
    frontend_dest = os.path.join(BUILD_DIR, "frontend")
    shutil.copytree(
        os.path.join(ROOT_DIR, "frontend"),
        frontend_dest,
        ignore=shutil.ignore_patterns(".DS_Store", "Thumbs.db")
    )
    os.makedirs(os.path.join(frontend_dest, "assets"), exist_ok=True)

    # 3. Copy Docs & Meta
    docs_dest = os.path.join(BUILD_DIR, "docs")
    if os.path.exists(os.path.join(ROOT_DIR, "docs")):
        shutil.copytree(os.path.join(ROOT_DIR, "docs"), docs_dest)

    shutil.copy2(os.path.join(ROOT_DIR, "README.md"), os.path.join(BUILD_DIR, "README.md"))
    shutil.copy2(os.path.join(ROOT_DIR, ".gitignore"), os.path.join(BUILD_DIR, ".gitignore"))
    shutil.copy2(os.path.join(ROOT_DIR, ".env.example"), os.path.join(BUILD_DIR, ".env.example"))
    
    # 4. Copy Docker Files
    for dfile in ["Dockerfile", "docker-compose.yml", ".dockerignore"]:
        p = os.path.join(ROOT_DIR, dfile)
        if os.path.exists(p):
            shutil.copy2(p, os.path.join(BUILD_DIR, dfile))

    # 5. Create Production Launch Scripts
    bat_content = """@echo off
TITLE Factify AI - Production Server
echo ===================================================
echo   Starting Factify AI Production Server (Waitress)
echo   Access URL: http://127.0.0.1:5002
echo ===================================================
cd backend
python wsgi.py
if errorlevel 1 (
    py -3.14 wsgi.py
)
pause
"""
    with open(os.path.join(BUILD_DIR, "run_production.bat"), "w", encoding="utf-8") as f:
        f.write(bat_content)

    sh_content = """#!/usr/bin/env bash
echo "==================================================="
echo "  Starting Factify AI Production Server (Gunicorn)"
echo "  Access URL: http://127.0.0.1:5002"
echo "==================================================="
cd backend
gunicorn --bind 0.0.0.0:5002 --workers 4 --timeout 120 wsgi:app
"""
    with open(os.path.join(BUILD_DIR, "run_production.sh"), "w", encoding="utf-8") as f:
        f.write(sh_content)

    # Clean intermediate caches inside build
    clean_caches(BUILD_DIR)

def create_zip():
    """Packages the build into a portable zip archive."""
    zip_filename = f"factify-v{VERSION}.zip"
    zip_path = os.path.join(DIST_DIR, zip_filename)
    log(f"Creating release archive: {zip_filename}...", "🗜️")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(BUILD_DIR):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, BUILD_DIR)
                zipf.write(full_path, arcname=os.path.join("factify", rel_path))

    size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    log(f"Archive created successfully: {size_mb:.2f} MB", "✅")
    return zip_path

def main():
    start_time = datetime.now()
    print("=" * 65)
    print("  🚀 FACTIFY AI — PRODUCTION BUILD PROCESS")
    print(f"  Version: {VERSION} | Timestamp: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)

    clean_caches(ROOT_DIR)
    validate_sources()
    assemble_release()
    zip_path = create_zip()

    duration = (datetime.now() - start_time).total_seconds()
    print("=" * 65)
    log(f"BUILD COMPLETED IN {duration:.2f} SECONDS", "🎉")
    print(f"  • Production Folder:  dist/factify-release/")
    print(f"  • Release Archive:    dist/factify-v{VERSION}.zip")
    print(f"  • Docker Build Ready: Dockerfile & docker-compose.yml")
    print("=" * 65)

if __name__ == "__main__":
    main()
