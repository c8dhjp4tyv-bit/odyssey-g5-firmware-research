"""Apply only unique, debug-backed symbols to an open IDA database.

Set ODYSSEY_SYMBOLS_CSV to main_symbol_anchors.csv or
aux_symbol_anchors.csv. The script does not save the database.
"""

import csv
import os

import ida_name

path = os.environ.get("ODYSSEY_SYMBOLS_CSV")
if not path:
    raise RuntimeError("ODYSSEY_SYMBOLS_CSV is required")

applied = 0
skipped = 0
with open(path, newline="", encoding="utf-8") as handle:
    for row in csv.DictReader(handle):
        address = int(row["function_address"], 16)
        name = row["inferred_name"]
        if ida_name.set_name(
            address,
            name,
            ida_name.SN_CHECK | ida_name.SN_NOWARN,
        ):
            applied += 1
        else:
            skipped += 1

print(f"ODYSSEY_SYMBOLS applied={applied} skipped={skipped}")
