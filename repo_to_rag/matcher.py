"""
Pattern matching and language detection for repo-to-rag.
"""

from __future__ import annotations

import fnmatch
from pathlib import Path
import re
from typing import List


def glob_to_regex(pat: str) -> re.Pattern:
    """Translates standard glob patterns including recursive ** into regex."""
    i, n = 0, len(pat)
    res: List[str] = []
    while i < n:
        c = pat[i]
        if c == "*":
            if i + 1 < n and pat[i + 1] == "*":
                if i + 2 < n and pat[i + 2] == "/":
                    res.append("(?:.*/)?")
                    i += 3
                    continue
                else:
                    res.append(".*")
                    i += 2
                    continue
            else:
                res.append("[^/]*")
                i += 1
                continue
        elif c == "?":
            res.append("[^/]")
            i += 1
            continue
        else:
            res.append(re.escape(c))
            i += 1
    return re.compile(f'^{"".join(res)}$')


def match_glob_patterns(rel_path: str, patterns: List[str]) -> bool:
    """Matches a relative path against a list of glob patterns supporting recursive **."""
    normalized = rel_path.replace("\\", "/")
    for pattern in patterns:
        norm_pattern = pattern.replace("\\", "/")
        try:
            rx = glob_to_regex(norm_pattern)
            if rx.match(normalized):
                return True
        except Exception:
            if fnmatch.fnmatch(normalized, norm_pattern):
                return True
    return False


def get_file_language(path: Path) -> str:
    """Maps file extension to markdown code fence language tag."""
    ext = path.suffix.lower()
    mapping = {
        ".py": "python",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".md": "markdown",
        ".html": "html",
        ".htm": "html",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".css": "css",
        ".scss": "scss",
        ".sh": "bash",
        ".bash": "bash",
        ".zsh": "bash",
        ".sql": "sql",
        ".toml": "toml",
        ".rs": "rust",
        ".go": "go",
        ".cpp": "cpp",
        ".cc": "cpp",
        ".cxx": "cpp",
        ".c": "c",
        ".h": "c",
        ".hpp": "cpp",
        ".java": "java",
        ".kt": "kotlin",
        ".rb": "ruby",
        ".php": "php",
        ".cs": "csharp",
        ".swift": "swift",
        ".lua": "lua",
        ".xml": "xml",
        ".proto": "protobuf",
    }
    return mapping.get(ext, "text")
