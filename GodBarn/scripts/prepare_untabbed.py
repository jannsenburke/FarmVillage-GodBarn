#!/usr/bin/env python3
"""Index God Barn's catalog rows that no Market tab lists, with Home overlay status.

Reads the recovered FarmVillage item records and imports the read-only
heritage_pricing module from that checkout. Writes only GodBarn/data/untabbed.json.
The companion never imports game code: it reads this index and each row's own
archived marketEntries. Run after prepare_archive.py, and again whenever
heritage_pricing.py changes. The overlay imports game modules, so run it with the
checkout's prepared environment: FarmVillage/LocalData/venv/bin/python.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from catalog_tools import UNTABBED_ORIGINS, has_market_entry  # noqa: E402

SOURCE = "xml/gz/v855038/items_opt.amf"
CACHE = "cache/gz_v855038_items_opt.json"
TARGET = ROOT / "data" / "untabbed.json"


def _scalar(value):
    return value[0] if isinstance(value, list) and value else value


def _positive(value):
    value = _scalar(value)
    if value in (None, "") or isinstance(value, bool):
        return None
    try:
        amount = int(float(value))
    except (TypeError, ValueError, OverflowError):
        return None
    return amount if amount > 0 else None


def _world_names(record):
    """World requirement names, in record order, read before the overlay rehomes them."""
    names = []

    def visit(node):
        if isinstance(node, dict):
            name = node.get("name")
            if node.get("className") == "World" and isinstance(name, str) and name and name not in names:
                names.append(name)
            for child in node.values():
                visit(child)
        elif isinstance(node, list):
            for child in node:
                visit(child)

    visit(record.get("requirements"))
    return names


def _home_price(record):
    market = _scalar(record.get("market")) or None
    if market == "cash":
        currency, amount = "cash", _positive(record.get("cash"))
    elif market in (None, "coins"):
        currency, amount = "coins", _positive(record.get("cost"))
    else:
        return None
    return {"currency": currency, "amount": amount} if amount else None


def first_indexes(records):
    """Map each name to its first record, the one God Barn and the game lookup use."""
    first = {}
    for index, record in enumerate(records):
        if isinstance(record, dict) and isinstance(record.get("name"), str):
            first.setdefault(record["name"], index)
    return first


def verify_against_catalog(records, first, catalog_path):
    """Refuse to index if God Barn's copied rows disagree with the game records."""
    copied = {}
    for item in json.loads(catalog_path.read_text(encoding="utf-8")):
        if isinstance(item, dict) and isinstance(item.get("name"), str):
            copied.setdefault(item["name"], item)
    if set(copied) != set(first):
        raise SystemExit("God Barn's catalog and the FarmVillage records name different items. Run prepare_archive.py first.")
    for name, index in first.items():
        raw = (copied[name].get("archive") or {}).get("raw") or {}
        if has_market_entry(records[index]) != has_market_entry(raw, item_type=copied[name].get("type")):
            raise SystemExit("Market tab data disagrees for " + name + ". Run prepare_archive.py first.")
    return len(copied)


def classify(records, first, heritage):
    """Return the origin entry for every name that no Market tab lists.

    Worlds and recovered prices are read before the overlay rewrites the records.
    The overlay itself is applied in memory only; the records are not written back.
    """
    pristine = {}
    for name, index in first.items():
        record = records[index]
        if not has_market_entry(record):
            priced = _positive(record.get("cash")) or _positive(record.get("cost"))
            pristine[name] = (_world_names(record), bool(priced))
    heritage.apply(records, server=True)
    origins = {}
    for name, (worlds, priced) in pristine.items():
        record = records[first[name]]
        if heritage.is_overlaid(record):
            entry = {"origin": "heritage"}
            home = _home_price(record)
            if home:
                entry["home"] = home
        elif not worlds and not priced:
            entry = {"origin": "exclusive"}
        else:
            entry = {"origin": "other"}
        if worlds:
            entry["worlds"] = worlds
        origins[name] = entry
    return origins


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Read-only FarmVillage checkout")
    args = parser.parse_args(argv)
    checkout = args.source.resolve()
    digest = hashlib.sha256((checkout / SOURCE).read_bytes()).hexdigest()
    cached = json.loads((checkout / CACHE).read_text(encoding="utf-8"))
    if (cached.get("identity") or {}).get("source_sha256") != digest:
        raise SystemExit("The FarmVillage item cache does not match items_opt.amf. Start FarmVillage once to rebuild it.")
    records = cached["data"]["settings"]["items"]["item"]
    first = first_indexes(records)
    names = verify_against_catalog(records, first, ROOT / "data" / "catalog.json")
    sys.path.insert(0, str(checkout))
    import heritage_pricing

    origins = classify(records, first, heritage_pricing)
    counts = {origin: sum(1 for entry in origins.values() if entry["origin"] == origin)
              for origin in UNTABBED_ORIGINS}
    document = {
        "schema": 1,
        "source": {"file": SOURCE, "sha256": digest, "records": len(records), "names": names},
        "heritage": {"enabled": bool(heritage_pricing.ENABLED), "digest": heritage_pricing.overlay_digest()},
        "counts": dict(counts, untabbed=len(origins)),
        "items": dict(sorted(origins.items())),
    }
    temporary = TARGET.with_suffix(".preparing.json")
    temporary.write_text(json.dumps(document, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    temporary.replace(TARGET)
    print(f"Indexed {len(origins):,} untabbed items: {counts['heritage']:,} heritage, "
          f"{counts['exclusive']:,} original exclusive, {counts['other']:,} other.")


if __name__ == "__main__":
    main()
