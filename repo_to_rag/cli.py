"""
CLI interface for repo-to-rag.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from repo_to_rag import __version__
from repo_to_rag.autodiscover import auto_discover_repository
from repo_to_rag.builder import RAGCorpusBuilder


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="repo-to-rag",
        description="Declarative repository-to-RAG corpus bundler for Google NotebookLM, Claude Projects, and high-context LLMs.",
    )
    parser.add_argument(
        "--config",
        "-c",
        type=str,
        help="Path to declarative JSON corpus manifest.",
    )
    parser.add_argument(
        "--repo",
        "-r",
        type=str,
        default=".",
        help="Root path of target repository (defaults to current working directory).",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=str,
        default="dist_rag",
        help="Destination directory for bundled Markdown volumes (defaults to dist_rag/).",
    )
    parser.add_argument(
        "--auto",
        "-a",
        action="store_true",
        help="Auto-discover repository architecture and generate volumes automatically.",
    )
    parser.add_argument(
        "--emit-config",
        type=str,
        help="Emit auto-discovered configuration to specified JSON path and exit.",
    )
    parser.add_argument(
        "--single-file",
        action="store_true",
        help="Also write a single monolithic Markdown file containing all volumes concatenated.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Dry run: inspect files and compute word counts without writing output.",
    )
    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version=f"repo-to-rag {__version__}",
    )

    args = parser.parse_args(argv)
    repo_root = Path(args.repo).resolve()
    out_dir = Path(args.output_dir)

    if not repo_root.is_dir():
        print(f"Error: repository path '{repo_root}' does not exist or is not a directory.", file=sys.stderr)
        return 1

    if args.auto:
        config = auto_discover_repository(repo_root)
        if args.emit_config:
            emit_path = Path(args.emit_config)
            emit_path.parent.mkdir(parents=True, exist_ok=True)
            emit_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
            print(f"Auto-discovered configuration emitted to {emit_path}")
            return 0
    elif args.config:
        config_path = Path(args.config)
        if not config_path.is_file():
            print(f"Error: configuration file '{config_path}' not found.", file=sys.stderr)
            return 1
        config = json.loads(config_path.read_text(encoding="utf-8"))
    else:
        # Check if local rag_manifest.json exists
        local_manifest = repo_root / "rag_manifest.json"
        if local_manifest.is_file():
            config = json.loads(local_manifest.read_text(encoding="utf-8"))
        else:
            print("No manifest specified and no rag_manifest.json found; running auto-discovery...", file=sys.stderr)
            config = auto_discover_repository(repo_root)

    builder = RAGCorpusBuilder(repo_root=repo_root, config=config, output_dir=out_dir)
    title = config.get("title", repo_root.name)

    print(f"Starting RAG Corpus compilation for '{title}'...")
    print(f"Repository Root:  {repo_root}")
    print(f"Output Directory: {out_dir}")
    print(f"Execution Mode:   {'DRY RUN (Check only)' if args.check else 'BUILD'}\n")

    results = builder.build_all(dry_run=args.check, single_file=args.single_file)

    print(f"{'Volume ID':<38} | {'Files':>5} | {'Words':>9} | {'Size (KB)':>9} | {'Status'}")
    print("-" * 80)
    for r in results:
        status = "OK" if not r["warning"] else r["warning"]
        kb = r["chars"] / 1024
        print(f"{r['id']:<38} | {r['file_count']:>5} | {r['words']:>9,} | {kb:>8.1f}K | {status}")
    print("-" * 80)

    total_files = sum(r["file_count"] for r in results)
    total_words = sum(r["words"] for r in results)
    total_mb = sum(r["chars"] for r in results) / 1024 / 1024

    print(f"Total: {len(results)} volumes | {total_files} files | {total_words:,} words | {total_mb:.2f} MB")
    if not args.check:
        print(f"\nCorpus successfully generated in: {out_dir}/")
        print(f"Master index written to: {out_dir / '00_CORPUS_INDEX.md'}")
        if args.single_file:
            print(f"Monolithic corpus written to: {out_dir / 'FULL_MONOLITHIC_CORPUS.md'}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
