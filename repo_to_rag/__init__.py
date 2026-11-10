"""
repo-to-rag: Declarative repository-to-RAG corpus bundler for Google NotebookLM,
Claude Projects, and high-context LLMs.
"""

__version__ = "1.0.0"

from repo_to_rag.builder import RAGCorpusBuilder
from repo_to_rag.autodiscover import auto_discover_repository
from repo_to_rag.converter import html_to_markdown
from repo_to_rag.matcher import match_glob_patterns, glob_to_regex

__all__ = [
    "__version__",
    "RAGCorpusBuilder",
    "auto_discover_repository",
    "html_to_markdown",
    "match_glob_patterns",
    "glob_to_regex",
]
