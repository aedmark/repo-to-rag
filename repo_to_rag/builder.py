"""
Core RAG corpus builder, compiler, and manifest processor.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Set

from repo_to_rag.converter import html_to_markdown
from repo_to_rag.matcher import get_file_language, match_glob_patterns


class RAGCorpusBuilder:
    """Discovers, validates, and builds RAG corpus volumes from configuration."""

    def __init__(self, repo_root: Path, config: Dict[str, Any], output_dir: Path) -> None:
        self.repo_root = repo_root.resolve()
        self.config = config
        self.output_dir = output_dir.resolve()
        self.global_exclusions = config.get("global_exclusions", [])
        self.limits = config.get(
            "limits",
            {
                "max_words_per_volume": 500000,
                "max_chars_per_volume": 3500000,
                "max_volumes": 50,
            },
        )
        self.volume_stats: List[Dict[str, Any]] = []

    def is_globally_excluded(self, rel_path: str) -> bool:
        return match_glob_patterns(rel_path, self.global_exclusions)

    def scan_volume_files(self, volume: Dict[str, Any]) -> List[Path]:
        """Resolves all matching files for a volume in prioritized order."""
        includes = volume.get("include", [])
        excludes = volume.get("exclude", [])
        priority_files = volume.get("priority_files", [])

        matched_files: Set[Path] = set()

        for root, dirs, files in os.walk(self.repo_root):
            rel_dir = os.path.relpath(root, self.repo_root).replace("\\", "/")
            if rel_dir == ".":
                rel_dir = ""

            # Prune globally excluded directories
            if rel_dir and self.is_globally_excluded(rel_dir):
                dirs[:] = []
                continue

            for f in files:
                file_path = Path(root) / f
                rel_path = os.path.relpath(file_path, self.repo_root).replace("\\", "/")

                if self.is_globally_excluded(rel_path):
                    continue
                if excludes and match_glob_patterns(rel_path, excludes):
                    continue

                if match_glob_patterns(rel_path, includes):
                    matched_files.add(file_path)

        # Sort priority files first, followed by remaining files alphabetically
        priority_paths = [
            (self.repo_root / p).resolve()
            for p in priority_files
            if (self.repo_root / p).resolve() in matched_files
        ]

        remaining = sorted(
            [p for p in matched_files if p not in priority_paths],
            key=lambda p: str(p.relative_to(self.repo_root)),
        )

        return priority_paths + remaining

    def render_file_markdown(self, file_path: Path, strip_html: bool) -> str:
        """Renders an individual file into formatted Markdown with metadata headers."""
        rel_path = str(file_path.relative_to(self.repo_root)).replace("\\", "/")
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return f"\n\n---\n# File: {rel_path}\n> ERROR READING FILE: {e}\n---\n\n"

        line_count = content.count("\n") + 1
        word_count = len(content.split())
        ext = file_path.suffix.lower()

        header = [
            "\n\n---",
            f"# File: {rel_path}",
            f"> Path: `{rel_path}` | Lines: {line_count} | Words: {word_count}",
            "---\n",
        ]

        if strip_html and ext in (".html", ".htm"):
            body = html_to_markdown(content)
        elif ext == ".md":
            body = content.strip()
        else:
            lang = get_file_language(file_path)
            body = f"```{lang}\n{content.strip()}\n```"

        return "\n".join(header) + "\n" + body + "\n"

    def build_volume(self, volume: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
        """Compiles a single volume into a self-contained Markdown document."""
        vol_id = volume["id"]
        title = volume["title"]
        desc = volume.get("description", "")
        strip_html = volume.get("strip_html", False)

        files = self.scan_volume_files(volume)
        parts: List[str] = [
            f"# {title}",
            f"\n> **Volume ID:** `{vol_id}`",
        ]

        if desc:
            parts.append(f"> **Subsystem Description:** {desc}")
        parts.append(f"> **Files Included:** {len(files)}")
        parts.append("\n## Table of Contents")

        for f in files:
            rel = str(f.relative_to(self.repo_root)).replace("\\", "/")
            slug = rel.replace("/", "-").replace(".", "-")
            parts.append(f"- [{rel}](#file-{slug})")

        total_words = 0
        total_chars = 0
        total_lines = 0

        for f in files:
            rendered = self.render_file_markdown(f, strip_html=strip_html)
            parts.append(rendered)
            words = len(rendered.split())
            chars = len(rendered)
            lines = rendered.count("\n")
            total_words += words
            total_chars += chars
            total_lines += lines

        full_text = "\n".join(parts)
        out_filename = f"{vol_id}.md"
        out_path = self.output_dir / out_filename

        if not dry_run:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            out_path.write_text(full_text, encoding="utf-8")

        max_words = self.limits.get("max_words_per_volume", 500000)
        warning = None
        if total_words > max_words:
            warning = f"EXCEEDS NOTEBOOKLM LIMIT: {total_words} words > {max_words} words"

        stats = {
            "id": vol_id,
            "title": title,
            "filename": out_filename,
            "file_count": len(files),
            "words": total_words,
            "chars": total_chars,
            "lines": total_lines,
            "warning": warning,
            "path": str(out_path),
            "content": full_text,
        }
        return stats

    def build_all(self, dry_run: bool = False, single_file: bool = False) -> List[Dict[str, Any]]:
        """Builds all volumes and generates the master corpus index and optional single file."""
        volumes = self.config.get("volumes", [])
        results: List[Dict[str, Any]] = []

        for vol in volumes:
            stats = self.build_volume(vol, dry_run=dry_run)
            results.append(stats)
            self.volume_stats.append(stats)

        if not dry_run:
            self.write_corpus_index(results)
            if single_file:
                self.write_single_file(results)

        return results

    def write_single_file(self, results: List[Dict[str, Any]]) -> None:
        """Concatenates all volumes into a single monolithic markdown file."""
        corpus_title = self.config.get("title", "Repository RAG Corpus")
        parts = [
            f"# {corpus_title}: Complete Unified Corpus",
            "\n> Generated by repo-to-rag.",
            "\n---\n",
        ]
        for r in results:
            parts.append(r["content"])
            parts.append("\n\n---\n\n")

        single_path = self.output_dir / "FULL_MONOLITHIC_CORPUS.md"
        single_path.write_text("\n".join(parts), encoding="utf-8")

    def write_corpus_index(self, results: List[Dict[str, Any]]) -> None:
        """Writes 00_CORPUS_INDEX.md summarizing all volumes and providing prompting guidance."""
        corpus_title = self.config.get("title", "Repository RAG Corpus")
        corpus_desc = self.config.get("description", "")
        target_sys = self.config.get("target_system", "notebooklm")

        total_files = sum(r["file_count"] for r in results)
        total_words = sum(r["words"] for r in results)
        total_chars = sum(r["chars"] for r in results)

        lines = [
            f"# {corpus_title}: Master RAG Corpus Index",
            "",
            f"> **Corpus Summary:** {corpus_desc}",
            f"> **Target System:** `{target_sys}`",
            f"> **Total Volumes:** {len(results)} | **Total Source Files:** {total_files} | **Total Word Count:** {total_words:,} words ({total_chars / 1024 / 1024:.2f} MB)",
            "",
            "## Volume Manifest",
            "",
            "| Volume File | Title | Files | Word Count | Status |",
            "| :--- | :--- | :---: | :---: | :--- |",
        ]

        for r in results:
            status = "Ready" if not r["warning"] else f"Warning: {r['warning']}"
            lines.append(
                f"| [`{r['filename']}`](./{r['filename']}) | {r['title']} | {r['file_count']} | {r['words']:,} | {status} |"
            )

        lines.extend([
            "",
            "## How to Use with Google NotebookLM",
            "",
            "1. **Upload Sources:**",
            "   - Open [Google NotebookLM](https://notebooklm.google.com/) and create a new notebook.",
            "   - Click **Add Sources** -> **Upload Files**.",
            "   - Select the generated `.md` volume files from this directory.",
            "2. **Generating Audio Overviews (Deep Dive Podcast):**",
            "   - In the Notebook Guide panel, click **Customize** under Audio Overview.",
            "   - Select the foundational architecture or narrative volumes to guide the hosts.",
            "   - Provide focus instructions (e.g. key trade-offs, architecture choices, philosophy).",
            "3. **Targeted Subsystem Inquiry:**",
            "   - Use the source checkmarks to isolate specific volumes for focused Q&A.",
            "   - Ask precise technical questions; responses cite exact source files and line ranges.",
            "",
            "## Volume Details and System Prompts",
            "",
        ])

        for r in results:
            vol_def = next((v for v in self.config.get("volumes", []) if v["id"] == r["id"]), {})
            desc = vol_def.get("description", "")
            lines.extend([
                f"### {r['title']} (`{r['filename']}`)",
                f"- **Description:** {desc}",
                f"- **Source Files:** {r['file_count']}",
                f"- **Word Count:** {r['words']:,}",
                f"- **Character Count:** {r['chars']:,}",
                "",
            ])

        index_path = self.output_dir / "00_CORPUS_INDEX.md"
        index_path.write_text("\n".join(lines), encoding="utf-8")
