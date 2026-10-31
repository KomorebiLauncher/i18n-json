#!/usr/bin/env python3
"""Pull translations from ParaTranz into the JSON catalogue.

This repository is where translations live: the translation platform edits them, this script
brings them back, and the i18n repository merges them into the .ts files it compiles.

Entries are matched by `key` (context + sha1 of the source), so a string whose source changed
comes in as a new key and the platform's old translation for the previous wording is ignored
rather than paired with text it does not belong to.

Usage:
    python tools/paratranz.py --token <token> [--dry-run] [--languages zh,de]
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import urllib.request

API = "https://paratranz.cn/api"
PAGE_SIZE = 1000
PROJECT = 21325


def fetch(url: str, token: str):
    request = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "User-Agent": "komorebi-i18n"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def project_files(token: str, project: int):
    return fetch(f"{API}/projects/{project}/files", token)


def strings_for_file(token: str, project: int, file_id: int):
    page = 1
    while True:
        data = fetch(f"{API}/projects/{project}/strings?page={page}&pageSize={PAGE_SIZE}&file={file_id}", token)
        yield from data.get("results", [])
        if page >= data.get("pageCount", 1):
            break
        page += 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--token", required=True)
    ap.add_argument("--project", type=int, default=PROJECT)
    ap.add_argument("--dir", default="json")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--languages", default="", help="comma separated, default all")
    args = ap.parse_args()

    root = pathlib.Path(args.dir)
    only = {s.strip() for s in args.languages.split(",") if s.strip()}
    totals = {"languages": 0, "updated": 0, "strings": 0}

    for entry in sorted(project_files(args.token, args.project), key=lambda f: f.get("name", "")):
        name = entry.get("name", "")
        if not name.endswith(".json"):
            continue
        lang = name[: -len(".json")]
        if only and lang not in only:
            continue
        path = root / f"{lang}.json"
        if not path.exists():
            print(f"skip {lang}: no export in this repository")
            continue

        entries = json.loads(path.read_text(encoding="utf-8"))
        known = {e["key"] for e in entries}
        incoming: dict[str, str] = {}
        for item in strings_for_file(args.token, args.project, entry["id"]):
            translation = (item.get("translation") or "").strip()
            if translation and item.get("stage", 1) >= 1 and item.get("key") in known:
                incoming[item["key"]] = translation
        totals["strings"] += len(incoming)

        updated = 0
        for e in entries:
            wanted = incoming.get(e["key"])
            if wanted and wanted != e["translation"]:
                e["translation"] = wanted
                updated += 1
            # a translation that came back is no longer unfinished
            if e["translation"] and "[unfinished]" in e["context"]:
                e["context"] = e["context"].replace(" | [unfinished]", "").replace("[unfinished]", "").strip(" |")

        totals["languages"] += 1
        totals["updated"] += updated
        if updated and not args.dry_run:
            path.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(f"{lang}: {len(incoming)} translated, {updated} changed{' (dry run)' if args.dry_run else ''}")

    print(json.dumps(totals, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
