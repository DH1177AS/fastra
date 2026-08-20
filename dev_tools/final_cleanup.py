import shutil
from pathlib import Path

BASE = Path.cwd()
dev_tools = BASE / "dev_tools"
legacy = BASE / "legacy"
dev_tools.mkdir(exist_ok=True)
legacy.mkdir(exist_ok=True)

root_scaffold = [
    "cleanup_project.py",
    "fix_test_019.py",
    "fix_test_020.py",
    "patch_api_determinism.py",
    "sprint4_5_lanjutan.py",
    "sprint4_5_tracelog_rules.py",
    "run_compliance.py",
]
for fname in root_scaffold:
    src = BASE / fname
    if src.exists():
        shutil.move(str(src), str(dev_tools / fname))
        print(f"✅ root/{fname} -> dev_tools")

# Legacy test yang memakai modul lama
for fname in ["test_aces400.py"]:
    src = BASE / "tests" / fname
    if src.exists():
        shutil.move(str(src), str(legacy / fname))
        print(f"✅ tests/{fname} -> legacy")

# Update run_api.py
run_api_content = '''import uvicorn

if __name__ == "__main__":
    uvicorn.run("api_secure:app", host="127.0.0.1", port=8000, reload=True)
'''
(BASE / "run_api.py").write_text(run_api_content, encoding="utf-8")
print("✅ run_api.py diupdate ke api_secure")

print("\n--- ROOT PYTHON FILES ---")
for f in sorted(BASE.glob("*.py")):
    print(f"  {f.name}")
print("\n--- COMPILER FILES ---")
for f in sorted((BASE / "fastra_core" / "compiler").glob("*.py")):
    print(f"  {f.name}")
print("\n✅ Pembersihan final selesai.")
