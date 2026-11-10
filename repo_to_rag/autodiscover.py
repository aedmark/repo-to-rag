"""
Heuristic repository analyzer and manifest generator.
"""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any, Dict


def auto_discover_repository(repo_path: Path) -> Dict[str, Any]:
    """Inspects an arbitrary codebase and derives a structured RAG volume manifest."""
    repo_name = repo_path.resolve().name
    manifest: Dict[str, Any] = {
        "$schema": "https://github.com/aedmark/repo-to-rag/schemas/rag_corpus.schema.json",
        "corpus_id": re.sub(r"[^a-z0-9_-]", "_", repo_name.lower()),
        "title": f"{repo_name} Repository Corpus",
        "description": f"Automated RAG corpus extracted from {repo_name} codebase.",
        "target_system": "notebooklm",
        "limits": {
            "max_words_per_volume": 500000,
            "max_chars_per_volume": 3500000,
            "max_volumes": 50,
        },
        "global_exclusions": [
            "**/.git/**",
            "**/.venv/**",
            "**/venv/**",
            "**/__pycache__/**",
            "**/*.pyc",
            "**/node_modules/**",
            "**/dist/**",
            "**/build/**",
            "**/target/**",
            "**/scratch/**",
            "**/logs/**",
            "**/saves/**",
            "**/output/**",
            "**/tmp/**",
            "**/temp/**",
            "**/cache/**",
            "**/.idea/**",
            "**/.vscode/**",
            "**/*.log",
            "**/*.db",
            "**/*.sqlite*",
            "**/*.lock",
        ],
        "volumes": [],
    }

    ignored_dir_names = {
        "docs", "doc", "tests", "test", "tools", "scripts", "lore",
        "config", "scratch", "logs", "saves", "output", "memories",
        "cache", "tmp", "temp", "node_modules", "target", "build", "dist",
        "test_telemetry_logs", "magicmock", "site-packages", "__pycache__",
        ".pytest_cache", ".git", ".idea", ".vscode", ".venv", "venv"
    }

    top_dirs = [
        d.name for d in repo_path.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    ]

    # 1. Documentation volume
    manifest["volumes"].append({
        "id": "01_documentation_and_architecture",
        "title": "Documentation, Architecture & Guides",
        "description": "High-level guides, architectural records, design specs, and documentation.",
        "include": ["*.md", "docs/**", "doc/**", "*.rst"],
        "priority_files": ["README.md", "docs/ARCHITECTURE.md", "docs/DECISIONS.md"],
    })

    # 2. Source code directories grouped logically
    src_dirs = [d for d in top_dirs if d.lower() not in ignored_dir_names]
    if src_dirs:
        # Group source directories into 1 to 4 volumes depending on count
        chunk_size = max(1, len(src_dirs) // 3)
        vol_num = 2
        for i in range(0, len(src_dirs), chunk_size):
            group = src_dirs[i:i + chunk_size]
            includes = [f"{g}/**" for g in group]
            manifest["volumes"].append({
                "id": f"{vol_num:02d}_{'_'.join(group)[:30]}",
                "title": f"Source Subsystems: {', '.join(group)}",
                "description": f"Implementation code for subsystems: {', '.join(group)}.",
                "include": includes,
            })
            vol_num += 1

    # 3. Configurations and factory data
    manifest["volumes"].append({
        "id": f"{len(manifest['volumes']) + 1:02d}_config_and_schemas",
        "title": "Configuration, Schemas & Static Data",
        "description": "JSON/YAML configurations, schemas, and static data dictionaries.",
        "include": ["*.json", "*.yaml", "*.yml", "*.toml", "lore/**", "config/**"],
    })

    # 4. Tests and verification
    if (repo_path / "tests").exists() or (repo_path / "test").exists():
        manifest["volumes"].append({
            "id": f"{len(manifest['volumes']) + 1:02d}_tests_and_verification",
            "title": "Test Suites & Verification Contracts",
            "description": "Unit tests, behavioral tests, and verification test suites.",
            "include": ["tests/**", "test/**"],
        })

    return manifest
