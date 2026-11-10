from pathlib import Path
from repo_to_rag.matcher import glob_to_regex, match_glob_patterns, get_file_language


def test_glob_to_regex_recursive():
    rx = glob_to_regex("body/**/*.py")
    assert rx.match("body/metabolism.py")
    assert rx.match("body/deep/nested/file.py")
    assert not rx.match("other/metabolism.py")


def test_glob_to_regex_simple():
    rx = glob_to_regex("*.md")
    assert rx.match("README.md")
    assert not rx.match("docs/README.md")


def test_match_glob_patterns():
    patterns = ["docs/*.md", "src/**/*.py", "**/.git/**"]
    assert match_glob_patterns("docs/ARCHITECTURE.md", patterns)
    assert match_glob_patterns("src/core/main.py", patterns)
    assert match_glob_patterns(".git/config", patterns)
    assert match_glob_patterns("sub/.git/HEAD", patterns)
    assert not match_glob_patterns("README.md", patterns)


def test_get_file_language():
    assert get_file_language(Path("test.py")) == "python"
    assert get_file_language(Path("config.json")) == "json"
    assert get_file_language(Path("deploy.yaml")) == "yaml"
    assert get_file_language(Path("index.html")) == "html"
    assert get_file_language(Path("script.sh")) == "bash"
    assert get_file_language(Path("main.rs")) == "rust"
    assert get_file_language(Path("unknown.xyz")) == "text"
