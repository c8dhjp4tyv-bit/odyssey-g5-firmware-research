import csv
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "docs" / "generated"


def rows(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class GeneratedCompletenessTests(unittest.TestCase):
    def test_byte_manifest_is_gap_free(self):
        manifest = rows(GENERATED / "byte_classification.csv")
        cursor = 0
        for row in manifest:
            self.assertEqual(int(row["start"], 16), cursor)
            cursor = int(row["end"], 16)
            self.assertIn(
                row["classification"],
                {
                    "HEADER",
                    "CHECKSUM",
                    "PADDING",
                    "DATA",
                    "UNRESOLVED",
                    "UNRESOLVED_MIXED_CODE_DATA",
                },
            )
        self.assertEqual(cursor, 0x34A3A0)

    def test_every_function_field_is_explicit(self):
        registry = rows(GENERATED / "function_registry.csv")
        self.assertEqual(len(registry), 4740)
        required = {
            "function_id",
            "architecture",
            "record",
            "runtime_address",
            "file_offset",
            "size",
            "name",
            "callers",
            "callees",
            "parameters",
            "return_value",
            "side_effects",
            "confidence",
            "sources",
            "unresolved_reason",
        }
        for row in registry:
            self.assertTrue(required.issubset(row))
            for field in required:
                self.assertNotEqual(row[field], "")
            if "UNRESOLVED" in " ".join(row.values()):
                self.assertNotEqual(row["unresolved_reason"], "NONE")

    def test_function_registry_matches_cross_tool_union(self):
        registry = rows(GENERATED / "function_registry.csv")
        by_record = {}
        for row in registry:
            by_record[row["record"]] = by_record.get(row["record"], 0) + 1
        self.assertEqual(
            by_record,
            {"0": 53, "1": 316, "2": 80, "3": 69, "5": 3625, "7": 597},
        )

    def test_every_indirect_site_is_classified(self):
        detailed = rows(GENERATED / "indirect_control_flow_detailed.csv")
        main = rows(GENERATED / "main_indirect_control_flow.csv")
        i8051 = rows(GENERATED / "8051_computed_jumps.csv")
        self.assertEqual(len(detailed), len(main) + len(i8051))
        for row in detailed:
            self.assertTrue(row["dispatch_class"])
            self.assertTrue(row["resolution_status"])
            self.assertTrue(row["evidence"])

    def test_ghidra_catalogs_retain_only_stable_function_starts(self):
        catalogs = sorted((GENERATED / "ghidra").glob("ghidra_*_functions.csv"))
        self.assertEqual(len(catalogs), 6)
        for catalog in catalogs:
            with catalog.open(newline="", encoding="utf-8") as handle:
                reader = csv.DictReader(handle)
                self.assertEqual(reader.fieldnames, ["address"], catalog.name)
                self.assertTrue(
                    all(row["address"].startswith("0x") for row in reader)
                )

    def test_8051_direct_call_edges_are_explicit(self):
        edges = rows(GENERATED / "8051_direct_call_edges.csv")
        self.assertEqual(len(edges), 975)
        self.assertEqual(
            set(edges[0]),
            {"record_index", "site", "file_offset", "target", "target_internal"},
        )

    def test_hardware_target_catalog_accounts_for_all_targets(self):
        accesses = rows(GENERATED / "main_absolute_memory_refs.csv")
        targets = rows(GENERATED / "hardware_absolute_accesses.csv")
        self.assertEqual(
            len(targets), len({row["target"] for row in accesses})
        )
        for row in targets:
            self.assertTrue(row["target_class"])
            self.assertTrue(row["bit_semantics"])

    def test_data_structures_have_unknown_field_accounting(self):
        structures = rows(GENERATED / "data_structure_catalog.csv")
        self.assertGreaterEqual(len(structures), 20)
        for row in structures:
            self.assertTrue(row["layout"])
            self.assertTrue(row["evidence"])
            self.assertTrue(row["unresolved_fields"])
