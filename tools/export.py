#!/usr/bin/env python3
"""Turn the .ts catalogue in the i18n repository into one JSON file per language.

The output is what translations are edited in: a flat array of entries with a stable `key`, the
`original` string, the current `translation` (empty when it still needs one) and a `context`
string built from Qt's context name, the string's extra comment, and flags.

Pass `--keep json` to keep translations that are newer than the catalogue: a translation written
into the JSON files since the last merge wins over the one in the .ts files, so the weekly refresh
can pick up new and reworded source strings without throwing away work in progress.

Usage:
    python tools/export.py --catalogue ../i18n --out json [--keep json]
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import pathlib
import re


def text_of(fragment: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", fragment))


def parse(path: pathlib.Path):
    """Return the ordered (context, source) list plus a lookup with translation state."""
    raw = path.read_text(encoding="utf-8")
    order: list[tuple[str, str]] = []
    data: dict[tuple[str, str], tuple[str, str, str, bool]] = {}

    for ctx in re.findall(r"<context>(.*?)</context>", raw, re.S):
        name_m = re.search(r"<name>(.*?)</name>", ctx, re.S)
        name = text_of(name_m.group(1)).strip() if name_m else ""
        for msg in re.findall(r"<message(.*?)</message>", ctx, re.S):
            src_m = re.search(r"<source>(.*?)</source>", msg, re.S)
            if not src_m:
                continue
            source = text_of(src_m.group(1))
            extra_m = re.search(r"<extracomment>(.*?)</extracomment>", msg, re.S)
            extra = text_of(extra_m.group(1)).strip() if extra_m else ""
            forms = re.findall(r"<numerusform>(.*?)</numerusform>", msg, re.S)
            tr_m = re.search(r"<translation([^>]*)>(.*?)</translation>", msg, re.S)

            # Strings the source no longer has are kept in the .ts as vanished; skip them.
            if tr_m and 'type="vanished"' in tr_m.group(1):
                continue

            unfinished = bool(tr_m and 'type="unfinished"' in tr_m.group(1))
            if forms:
                translation = "\n".join(text_of(f) for f in forms)
            elif tr_m:
                translation = text_of(tr_m.group(2)).strip() if tr_m.group(2).strip() else ""
            else:
                translation = ""

            state = "unfinished" if unfinished and translation else ("untranslated" if not translation else "")
            if (name, source) not in data:
                order.append((name, source))
            data[(name, source)] = (translation, state, extra, bool(forms))

    return order, data


def existing_translations(path: pathlib.Path) -> dict[str, str]:
    """Translations already in the JSON export, keyed by the stable key."""
    if not path.exists():
        return {}
    return {e["key"]: e["translation"] for e in json.loads(path.read_text(encoding="utf-8")) if e.get("translation")}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalogue", required=True, help="checkout of the i18n repository")
    ap.add_argument("--out", required=True, help="directory to write {lang}.json into")
    ap.add_argument("--keep", help="directory with the current {lang}.json files whose translations win over the catalogue")
    args = ap.parse_args()

    catalogue = pathlib.Path(args.catalogue)
    out_dir = pathlib.Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    template_order, _ = parse(catalogue / ".template.ts")
    languages = sorted(p for p in catalogue.glob("*.ts") if p.name != ".template.ts")

    manifest = {"strings": len(template_order), "languages": {}}
    kept_total = 0
    for ts in languages:
        _, translations = parse(ts)
        earlier = {}
        if args.keep:
            earlier = existing_translations(pathlib.Path(args.keep) / f"{ts.stem}.json")
        entries = []
        for name, source in template_order:
            translation, state, extra, plural = translations.get((name, source), ("", "untranslated", "", False))
            key = f"{name}:{hashlib.sha1(source.encode('utf-8')).hexdigest()[:12]}"
            if earlier.get(key):
                if earlier[key] != translation:
                    kept_total += 1
                translation = earlier[key]
            ctx_bits = [name] if name else []
            if extra:
                ctx_bits.append(extra)
            flags = [f for f, on in (("unfinished", state == "unfinished"), ("plural", plural)) if on]
            if flags:
                ctx_bits.append("[" + ", ".join(flags) + "]")
            entries.append(
                {
                    "key": key,
                    "original": source,
                    "translation": translation,
                    "context": " | ".join(b for b in ctx_bits if b),
                }
            )

        lang = ts.stem
        (out_dir / f"{lang}.json").write_text(
            json.dumps(entries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
        )
        done = sum(1 for e in entries if e["translation"])
        manifest["languages"][lang] = {"translated": done, "missing": len(entries) - done}

    (out_dir.parent / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(f"{len(languages)} languages, {len(template_order)} strings each, {kept_total} translations kept from {args.keep or 'nowhere'}")


if __name__ == "__main__":
    main()
