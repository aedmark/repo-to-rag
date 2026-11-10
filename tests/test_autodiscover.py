import tempfile
from pathlib import Path
from repo_to_rag.autodiscover import auto_discover_repository


def test_autodiscover_detects_structure():
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo = Path(tmp_dir) / "sample_app"
        repo.mkdir()
        (repo / "README.md").write_text("# Sample App")
        (repo / "src").mkdir()
        (repo / "src" / "index.js").write_text("console.log('test');")
        (repo / "config").mkdir()
        (repo / "config" / "settings.json").write_text("{}")
        (repo / "tests").mkdir()
        (repo / "tests" / "test_app.js").write_text("// test")

        manifest = auto_discover_repository(repo)
        assert manifest["corpus_id"] == "sample_app"
        assert len(manifest["volumes"]) >= 3

        vol_ids = [v["id"] for v in manifest["volumes"]]
        assert "01_documentation_and_architecture" in vol_ids
        assert any("tests" in vid for vid in vol_ids)
        assert any("config" in vid for vid in vol_ids)
