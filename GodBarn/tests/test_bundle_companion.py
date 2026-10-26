"""Native resources preserve full artwork mappings without copying farms."""
import gzip
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("god_barn_native_bundler", ROOT / "scripts/bundle_companion.py")
bundler = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bundler)


class NativeArchiveBundleTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="god-barn-bundle-", dir="/private/tmp" if Path("/private/tmp").is_dir() else None)
        self.base = Path(self.temporary.name)
        self.source = self.base / "GodBarn"
        for name in ("__init__.py", "engine.py", "integration.py", "seasonal.py", "encyclopedia.py",
                     "progression_tools.py", "catalog_tools.py", "helper_tools.py",
                     "static/index.html", "static/app.js", "static/style.css", "static/farmville.css",
                     "static/touch.js"):
            path = self.source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("fixture resource")
        self.write("data/rules.json", {"levels": []})
        self.write("data/helpers.json", {"schema": 1, "collections": [], "quests": []})
        self.untabbed = {"schema": 1, "items": {"pinkcow": {"origin": "other"}}}
        self.write("data/untabbed.json", self.untabbed)
        self.catalog = [{"name": "pinkcow", "image": "/static/assets/items/pink-cow.png",
                         "artwork": {"status": "exact", "logical": "assets/animals/pinkcow_icon.png"}}]
        self.write("data/catalog.json", self.catalog)
        self.original = self.base / "FarmVillage"
        self.write("data/provenance.json", {"sourceDirectory": str(self.original), "assets": []})
        self.destination = self.base / "staged"

    def tearDown(self):
        self.temporary.cleanup()

    def write(self, name, data):
        path = self.source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data))

    def test_all_declared_raster_mappings_keep_nested_source_paths_and_placeholder(self):
        mappings = {
            "static/assets/items/pink-cow.png": "animals/pink-hash.png",
            "static/assets/items/hat.gif": "clothes/season/hat-hash.gif",
            "static/assets/items/tree.webp": "trees/holiday/tree-hash.webp",
            "static/assets/items/flower.jpg": "decorations/flower-hash.jpeg",
        }
        self.write("data/provenance.json", {"sourceDirectory": str(self.original), "assets": [
            {"path": copied, "originalPath": str(self.original / "LocalData/assets" / relative)}
            for copied, relative in mappings.items()]})
        placeholder = self.source / "static/assets/ui/missing-art.svg"
        placeholder.parent.mkdir(parents=True, exist_ok=True)
        placeholder.write_text("<svg xmlns='http://www.w3.org/2000/svg'/>")
        helper_art = self.source / "static/assets/helper-art/quest.png"
        helper_art.parent.mkdir(parents=True, exist_ok=True)
        helper_art.write_bytes(b"original quest picture")
        ribbon_art = self.source / "static/assets/progression/blue.png"
        ribbon_art.parent.mkdir(parents=True, exist_ok=True)
        ribbon_art.write_bytes(b"original blue ribbon picture")
        copied_item = self.source / "static/assets/items/pink-cow.png"
        copied_item.parent.mkdir(parents=True, exist_ok=True)
        copied_item.write_bytes(b"original image bytes")
        self.write("workspace/farms/private.json", {"private": "farm"})
        audit = {"sourceReadOnly": True, "catalogUniqueItems": 1, "missingUniqueItems": 0}
        self.write("data/catalog-audit.json", audit)
        bundler.bundle_companion(self.source, self.destination)
        self.assertEqual(json.loads((self.destination / "data/asset-map.json").read_text()), mappings)
        self.assertEqual(json.loads(gzip.decompress((self.destination / "data/catalog.json.gz").read_bytes())), self.catalog)
        self.assertEqual((self.destination / "static/assets/ui/missing-art.svg").read_bytes(), placeholder.read_bytes())
        self.assertEqual((self.destination / "static/assets/helper-art/quest.png").read_bytes(), helper_art.read_bytes())
        self.assertEqual((self.destination / "static/assets/progression/blue.png").read_bytes(), ribbon_art.read_bytes())
        self.assertTrue((self.destination / "catalog_tools.py").is_file())
        self.assertTrue((self.destination / "helper_tools.py").is_file())
        self.assertEqual((self.destination / "data/helpers.json").read_bytes(),
                         (self.source / "data/helpers.json").read_bytes())
        self.assertEqual(json.loads((self.destination / "data/catalog-audit.json").read_text()), audit)
        self.assertEqual(json.loads((self.destination / "data/untabbed.json").read_text()), self.untabbed)
        self.assertFalse((self.destination / "static/assets/items").exists())
        self.assertFalse((self.destination / "workspace").exists())

    def test_missing_shared_discovery_helper_fails_before_building_a_broken_runtime(self):
        (self.source / "catalog_tools.py").unlink()
        with self.assertRaisesRegex(ValueError, "catalog_tools.py"):
            bundler.bundle_companion(self.source, self.destination)
        self.assertFalse(self.destination.exists())

    def test_missing_untabbed_index_fails_before_staging_incomplete_market_labels(self):
        (self.source / "data/untabbed.json").unlink()
        with self.assertRaisesRegex(ValueError, "data/untabbed.json"):
            bundler.bundle_companion(self.source, self.destination)
        self.assertFalse(self.destination.exists())

    def test_untabbed_index_cannot_be_a_symlink(self):
        index = self.source / "data/untabbed.json"
        index.unlink()
        index.symlink_to(self.source / "data/rules.json")
        with self.assertRaisesRegex(ValueError, "data/untabbed.json"):
            bundler.bundle_companion(self.source, self.destination)
        self.assertFalse(self.destination.exists())

    def test_missing_progression_helper_fails_before_building_a_broken_runtime(self):
        (self.source / "progression_tools.py").unlink()
        with self.assertRaisesRegex(ValueError, "progression_tools.py"):
            bundler.bundle_companion(self.source, self.destination)

    def test_missing_collection_and_quest_helper_fails_before_staging(self):
        (self.source / "helper_tools.py").unlink()
        with self.assertRaisesRegex(ValueError, "helper_tools.py"):
            bundler.bundle_companion(self.source, self.destination)
        self.assertFalse(self.destination.exists())

    def test_original_artwork_mapping_cannot_escape_source_asset_root(self):
        for original in (self.base / "secret.png", self.original / "LocalData/assets/../private.png"):
            with self.subTest(original=original):
                self.write("data/provenance.json", {"sourceDirectory": str(self.original), "assets": [
                    {"path": "static/assets/items/cow.png", "originalPath": str(original)}]})
                # Failure can leave a partial stage, so each attempt gets a fresh destination.
                destination = self.base / ("stage-" + str(len(list(self.base.glob("stage-*")))))
                with self.assertRaises(ValueError):
                    bundler.bundle_companion(self.source, destination)


if __name__ == "__main__":
    unittest.main()
