#!/usr/bin/env python3
"""
scan_legacy.py

Сканирует репозиторий на артефакты legacy v1 и делает отчёт.
Поддерживает dry-run (по умолчанию) и авто-фикс: delete/shim.
"""
import argparse, json, os, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

LEGACY_FILE_CANDIDATES = [
    "main.py",                           # старая точка входа
    "core/keyboards/inline.py",          # монолит из v1
    "core/utils/i18n.py",                # старое расположение i18n
    "core/exceptions.py",                # старый модуль исключений
]

LEGACY_IMPORT_PATTERNS = [
    r"from\s+core\.utils\.i18n\s+import",
    r"import\s+core\.utils\.i18n",
    r"from\s+core\.exceptions\s+import",
    r"\bselect_restoran\b",
    r"\bregional_restoran\b",
]

REQUIRED_V2_ANCHORS = [
    "main_v2.py",
    "core/logger.py",
    "locales/ru.json",
    "locales/en.json",
    "migrations",
]


def exists(p: str) -> bool:
    return (ROOT / p).exists()


def glob(pattern: str):
    return list(ROOT.rglob(pattern))


def scan():
    report = {
        "anchors_v2_missing": [],
        "legacy_files_found": [],
        "legacy_imports_found": [],
        "migrations_v2_like": [],
        "advice": [],
    }

    # 1) v2 anchors
    for anchor in REQUIRED_V2_ANCHORS:
        if not exists(anchor):
            report["anchors_v2_missing"].append(anchor)

    # 2) legacy files
    for f in LEGACY_FILE_CANDIDATES:
        p = ROOT / f
        if p.exists():
            report["legacy_files_found"].append(str(p.relative_to(ROOT)))

    # 3) legacy imports occurrences
    patterns = [re.compile(p) for p in LEGACY_IMPORT_PATTERNS]
    for path in ROOT.rglob("*.py"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        hits = []
        for pat in patterns:
            for m in pat.finditer(text):
                line_no = text[: m.start()].count("\n") + 1
                hits.append({"line": line_no, "match": m.group(0)})
        if hits:
            report["legacy_imports_found"].append({
                "file": str(path.relative_to(ROOT)),
                "hits": hits,
            })

    # 4) v2-like migrations (heuristic)
    for p in glob("migrations/*"):
        name = p.name.lower()
        if "v2" in name or "_v2" in name:
            report["migrations_v2_like"].append(str(p.relative_to(ROOT)))

    # 5) advices
    if "main.py" in report["legacy_files_found"]:
        report["advice"].append("Удалить main.py — использовать только main_v2.py")
    if any(x.endswith("core/keyboards/inline.py") for x in report["legacy_files_found"]):
        report["advice"].append("Разбить/удалить монолит core/keyboards/inline.py, если уже есть пакет inline/*")
    if any("core/utils/i18n.py" in x for x in report["legacy_files_found"]):
        report["advice"].append("Удалить core/utils/i18n.py (если перешли на core/i18n/*)")
    if not report["migrations_v2_like"]:
        report["advice"].append("Проверить наличие миграций *_v2*, при необходимости накатить вручную")

    return report


def delete_path(p: Path):
    if p.is_dir():
        for child in p.iterdir():
            delete_path(child)
        p.rmdir()
    else:
        p.unlink()


def apply_fix(report, mode: str):
    """
    mode:
      - "delete": жёстко удалить legacy-файлы
      - "shim": оставить файлы, но переписать их как тонкие прокси в v2 (без удаления)
    """
    changed = []

    # main.py
    p = ROOT / "main.py"
    if p.exists():
        if mode == "delete":
            delete_path(p); changed.append("deleted: main.py")
        elif mode == "shim":
            p.write_text(
                'import sys\nprint("Deprecated: use main_v2.py", file=sys.stderr)\nfrom main_v2 import *\n',
                encoding="utf-8",
            )
            changed.append("shimmed: main.py -> import main_v2")

    # keyboards inline monolith
    p = ROOT / "core/keyboards/inline.py"
    if p.exists():
        inline_pkg = ROOT / "core/keyboards/inline"
        if inline_pkg.exists() and inline_pkg.is_dir():
            if mode == "delete":
                delete_path(p); changed.append("deleted: core/keyboards/inline.py")
            elif mode == "shim":
                p.write_text("# Legacy shim: use core.keyboards.inline.* modules\n", encoding="utf-8")
                changed.append("shimmed: core/keyboards/inline.py")

    # i18n legacy
    p = ROOT / "core/utils/i18n.py"
    if p.exists():
        if mode == "delete":
            delete_path(p); changed.append("deleted: core/utils/i18n.py")
        elif mode == "shim":
            p.write_text("from core.i18n import *  # legacy shim\n", encoding="utf-8")
            changed.append("shimmed: core/utils/i18n.py -> core.i18n")

    # exceptions legacy
    p = ROOT / "core/exceptions.py"
    if p.exists():
        if mode == "delete":
            delete_path(p); changed.append("deleted: core/exceptions.py")
        elif mode == "shim":
            p.write_text(
                "try:\n"
                "    from core.common.exceptions import *\n"
                "except Exception:\n"
                "    from core.domain.exceptions import *  # legacy shim\n",
                encoding="utf-8",
            )
            changed.append("shimmed: core/exceptions.py -> common/domain")
    return changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true", help="вывести JSON отчёт")
    ap.add_argument("--fix", choices=["delete", "shim"], help="авто-фикс legacy (delete/shim)")
    ap.add_argument("--yes", action="store_true", help="подтвердить изменения без вопросов")
    args = ap.parse_args()

    report = scan()

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print("=== LEGACY SCAN REPORT ===")
        if report["anchors_v2_missing"]:
            print("Missing v2 anchors:", *report["anchors_v2_missing"], sep="\n  - ")
        print("\nLegacy files:")
        for f in report["legacy_files_found"] or ["(none)"]:
            print("  -", f)
        print("\nLegacy imports:")
        for hit in report["legacy_imports_found"] or []:
            print("  -", hit["file"])
            for h in hit["hits"]:
                print(f"      L{h['line']}: {h['match']}")
        if not report["legacy_imports_found"]:
            print("  (none)")
        print("\nV2-like migrations:", report["migrations_v2_like"] or "(none)")
        print("\nAdvice:")
        for a in report["advice"] or ["(none)"]:
            print("  -", a)

    if args.fix:
        if not args.yes:
            print("\n--fix указан, но нет --yes. Ничего не меняю.")
            return 0
        changed = apply_fix(report, args.fix)
        print("\nApplied changes:")
        for c in changed or ["(nothing)"]:
            print("  -", c)


if __name__ == "__main__":
    sys.exit(main())


