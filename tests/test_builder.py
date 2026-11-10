import tempfile
from pathlib import Path
from repo_to_rag.builder import RAGCorpusBuilder


def test_builder_runs_and_creates_volume():
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo = Path(tmp_dir) / "test_repo"
        repo.mkdir()
        out = Path(tmp_dir) / "output"

        # Create dummy repo files
        (repo / "README.md").write_text("# Project Readme\nThis is a test readme.")
        (repo / "main.py").write_text("print('hello world')\n")
        sub = repo / "sub"
        sub.mkdir()
        (sub / "logic.py").write_text("def run():\n    return 42\n")

        config = {
            "corpus_id": "test_corpus",
            "title": "Test Corpus",
            "volumes": [
                {
                    "id": "01_docs",
                    "title": "Documentation",
                    "include": ["*.md"],
                },
                {
                    "id": "02_code",
                    "title": "Code",
                    "priority_files": ["main.py"],
                    "include": ["**/*.py"],
                },
            ],
        }

        builder = RAGCorpusBuilder(repo_root=repo, config=config, output_dir=out)
        results = builder.build_all(dry_run=False, single_file=True)

        assert len(results) == 2
        assert (out / "01_docs.md").exists()
        assert (out / "02_code.md").exists()
        assert (out / "00_CORPUS_INDEX.md").exists()
        assert (out / "FULL_MONOLITHIC_CORPUS.md").exists()

        code_md = (out / "02_code.md").read_text()
        assert "main.py" in code_md
        assert "sub/logic.py" in code_md
        # Priority file should appear before sub/logic.py
        pos_main = code_md.find("main.py")
        pos_sub = code_md.find("sub/logic.py")
        assert pos_main < pos_sub
