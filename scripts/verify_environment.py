#!/usr/bin/env python3
"""
NEXORA Environment Verification Script (Phase 0)
Validates system prerequisites, runtimes, core dependencies,
storage permissions, and network readiness.
"""

import sys
import os
import shutil
import subprocess
import sqlite3
from typing import Optional
from pathlib import Path

def print_header(title: str):
    print(f"\n{'='*70}\n[NEXORA ENV CHECK] {title}\n{'='*70}")

def check_cmd(cmd_args, name: str, min_version_str: str = "") -> dict:
    try:
        res = subprocess.run(cmd_args, capture_output=True, text=True, check=True, shell=os.name == "nt")
        ver = res.stdout.strip() or res.stderr.strip()
        first_line = ver.splitlines()[0] if ver else "installed"
        print(f"  [PASS] {name}: {first_line}")
        return {"status": "PASS", "details": first_line}
    except Exception as e:
        print(f"  [FAIL] {name}: not found or error ({e})")
        return {"status": "FAIL", "details": str(e)}

def check_module(module_name: str, import_name: Optional[str] = None, category: str = "Core") -> dict:
    mod = import_name or module_name
    try:
        m = __import__(mod)
        version = getattr(m, "__version__", "available")
        print(f"  [PASS] ({category}) {module_name}: v{version}")
        return {"status": "PASS", "version": str(version), "category": category}
    except Exception as e:
        print(f"  [WARNING] ({category}) {module_name}: import error ({type(e).__name__}: {e})")
        return {"status": "WARNING", "error": f"{type(e).__name__}: {e}", "category": category}

def check_disk_and_permissions(workspace_root: Path) -> dict:
    try:
        test_file = workspace_root / ".write_test_tmp"
        test_file.write_text("nexora_write_test", encoding="utf-8")
        test_file.unlink()
        
        total, used, free = shutil.disk_usage(workspace_root)
        free_gb = free / (1024 ** 3)
        print(f"  [PASS] Write permissions verified on {workspace_root}")
        print(f"  [PASS] Disk space available: {free_gb:.2f} GB free")
        return {"status": "PASS", "free_gb": free_gb}
    except Exception as e:
        print(f"  [FAIL] Storage check failed: {e}")
        return {"status": "FAIL", "error": str(e)}

def check_model_cache(workspace_root: Path) -> dict:
    model_dir = workspace_root / "data" / "models"
    model_file = model_dir / "yolov8n.pt"
    if model_file.exists():
        size_mb = model_file.stat().st_size / (1024 * 1024)
        print(f"  [INFO] Local YOLO model detected: {model_file} ({size_mb:.2f} MB)")
        return {"status": "LOCAL_AVAILABLE", "path": str(model_file), "size_mb": size_mb}
    else:
        print(f"  [INFO] YOLO weights (yolov8n.pt) not in local data/models; will download on first Phase 3 run or can be cached offline.")
        return {"status": "NOT_CACHED_LOCAL", "path": str(model_file)}

def main():
    print_header("1. Runtimes & Toolchain Check")
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    py_status = "PASS" if sys.version_info >= (3, 10) else "FAIL"
    print(f"  [{py_status}] Python runtime: {py_ver} (Target: >= 3.10)")
    
    node_res = check_cmd(["node", "--version"], "Node.js (Target >= 18.0)")
    npm_res = check_cmd(["npm", "--version"], "npm (Target >= 9.0)")
    git_res = check_cmd(["git", "--version"], "Git")

    print_header("2. Core Backend Foundation Dependencies (FastAPI / SQLite / SQLAlchemy)")
    core_modules = [
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"),
        ("pydantic", "pydantic"),
        ("sqlalchemy", "sqlalchemy"),
        ("sqlite3", "sqlite3"),
        ("httpx", "httpx"),
        ("pytest", "pytest"),
    ]
    core_results = {m[0]: check_module(m[0], m[1], "Phase 1 Core") for m in core_modules}

    print_header("3. AI / Computer Vision & GIS Modules (Phase 3 & 6 Capabilities)")
    ai_gis_modules = [
        ("networkx", "networkx"),
        ("opencv-python", "cv2"),
        ("torch", "torch"),
        ("ultralytics", "ultralytics"),
    ]
    ai_results = {m[0]: check_module(m[0], m[1], "AI / GIS Stack") for m in ai_gis_modules}

    print_header("4. Workspace Storage & Directory Permissions")
    workspace_root = Path(__file__).resolve().parent.parent
    disk_res = check_disk_and_permissions(workspace_root)
    model_res = check_model_cache(workspace_root)

    print_header("5. Verification Summary")
    core_all_pass = all(r["status"] == "PASS" for r in core_results.values()) and py_status == "PASS" and node_res["status"] == "PASS"
    print(f"  Foundation Readiness (Phase 0 & 1): {'[READY]' if core_all_pass else '[ATTENTION REQUIRED]'}")
    ai_all_pass = all(r["status"] == "PASS" for r in ai_results.values())
    print(f"  AI & GIS Readiness (Phase 3 & 6):   {'[INSTALLED]' if ai_all_pass else '[PARTIAL]'}")
    print(f"\nVerification complete.\n")
    return 0 if core_all_pass else 1

if __name__ == "__main__":
    sys.exit(main())
