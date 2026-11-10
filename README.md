# repo-to-rag

> Declarative repository-to-RAG corpus bundler for Google NotebookLM, Claude Projects, and high-context LLMs.

`repo-to-rag` transforms any repository into curated, structured Markdown volumes optimized for retrieval-augmented generation and deep codebase inquiry. Instead of dumping loose code into an AI model or uploading hundreds of fragmented files, `repo-to-rag` structures your codebase into semantic books with tables of contents, file metadata headers, and clean syntax boundaries.

---

## Why repo-to-rag?

Standard context windows struggle to hold entire production codebases, and uploading raw repos often causes citation noise, broken context, and token bloat.

Google NotebookLM provides a massive source capacity:
- Up to **50 sources per notebook**
- Up to **500,000 words per source**
- Built-in **Audio Overviews** (two-host Deep Dive podcasts discussing your architecture)
- Grounded citations citing exact files and sections

`repo-to-rag` bridges this gap:
1. **Curated Volumes:** Groups related subsystems (e.g. Architecture, Core Engine, State Models, CLI Tools, Test Contracts) into individual Markdown volumes.
2. **Strict Budget Caps:** Enforces word and character limits per volume, guaranteeing compliance with NotebookLM's 500,000-word source cap.
3. **High Signal, Zero Noise:** Filters binary files, virtual environments, caches, and large ephemeral data out of the corpus.
4. **Clean Code & Prose Formatting:** Preserves docstrings and comments, adds syntax-highlighted code fences, embeds priority architecture docs first, and cleans HTML devlogs into Markdown.
5. **Zero External Dependencies:** Built entirely with Python's standard library (3.9+).

---

## Installation

### Using pip
```bash
git clone https://github.com/aedmark/repo-to-rag.git
cd repo-to-rag
pip install .
```

### Direct CLI without Installation
You can also run it directly using any Python 3.9+ runtime:
```bash
python -m repo_to_rag.cli --help
```

---

## Quickstart

### 1. Auto-Discovery Mode (Any Repository)
Run `repo-to-rag` on any project directory without writing a configuration file:
```bash
repo-to-rag --repo /path/to/my-project --auto --output-dir dist_rag
```
`repo-to-rag` inspects the project, categorizes documentation, core subsystems, configurations, and test suites, and generates ready-to-upload Markdown volumes in `dist_rag/`.

### 2. Emit an Auto-Discovered Config for Customization
To inspect and customize the auto-discovered volume manifest:
```bash
repo-to-rag --repo /path/to/my-project --auto --emit-config my_project_manifest.json
```
Edit `my_project_manifest.json` to fine-tune volume boundaries, and then build:
```bash
repo-to-rag --config my_project_manifest.json --output-dir dist_rag
```

### 3. Dry-Run Check
To check file matches, volume word counts, and size budgets without writing any files:
```bash
repo-to-rag --config my_project_manifest.json --check
```

---

## Using with Google NotebookLM

1. **Upload Volumes:**
   - Go to [Google NotebookLM](https://notebooklm.google.com/) and create a new notebook.
   - Click **Add Sources** -> **Upload Files**.
   - Select the generated `.md` volume files from `dist_rag/`.
2. **Generating Audio Overviews (Deep Dive Podcast):**
   - Check the Architecture, Vision, and Devlog volumes.
   - Click **Customize** under Audio Overview in the Notebook Guide.
   - Give the AI hosts focus instructions (e.g. *"Discuss the design trade-offs, state management, and failure boundaries of this architecture"*).
   - Click **Generate**.
3. **Subsystem Cross-Examination:**
   - Use source checkmarks to isolate specific volumes (e.g. check only the database engine volume when asking database questions).
   - Ask complex questions like:
     - *"Trace the lifecycle of a request from the CLI down to storage."*
     - *"What architectural invariants are declared and where in the code are they enforced?"*
     - *"Identify potential race conditions in the worker queue based on the source code."*

---

## Declarative Manifest Schema

`repo-to-rag` is driven by a simple JSON manifest validated against [`schemas/rag_corpus.schema.json`](schemas/rag_corpus.schema.json):

```json
{
  "$schema": "https://github.com/aedmark/repo-to-rag/schemas/rag_corpus.schema.json",
  "corpus_id": "my_project",
  "title": "My Project Architecture & Source",
  "description": "Complete source code and technical documentation.",
  "target_system": "notebooklm",
  "limits": {
    "max_words_per_volume": 500000,
    "max_chars_per_volume": 3500000,
    "max_volumes": 50
  },
  "global_exclusions": [
    "**/.git/**",
    "**/.venv/**",
    "**/__pycache__/**",
    "**/*.pyc",
    "**/node_modules/**",
    "**/*.log",
    "**/*.db"
  ],
  "volumes": [
    {
      "id": "01_architecture_and_docs",
      "title": "Architecture & Epistemic Guides",
      "description": "Core system design, architecture decision records, and handoffs.",
      "priority_files": ["README.md", "docs/ARCHITECTURE.md"],
      "include": ["*.md", "docs/**"]
    },
    {
      "id": "02_core_engine",
      "title": "Core Engine & State Machine",
      "description": "Turn cycles, state transitions, and background loops.",
      "include": ["engine/**/*.py", "state/**/*.py"]
    }
  ]
}
```

### Volume Options
- `id`: File prefix (e.g. `01_architecture`).
- `title`: Display title in the index and headers.
- `description`: Contextual summary embedded at the head of the volume for the LLM.
- `priority_files`: Files placed at the very top of the volume (useful for priming the model with design documents before code).
- `include`: Glob patterns to include (supports recursive `**`).
- `exclude`: Volume-specific glob patterns to ignore.
- `strip_html`: When true, converts HTML documents into clean Markdown.

---

## CLI Reference

```text
usage: repo-to-rag [-h] [--config CONFIG] [--repo REPO] [--output-dir OUTPUT_DIR]
                   [--auto] [--emit-config EMIT_CONFIG] [--single-file]
                   [--check] [--version]

Declarative repository-to-RAG corpus bundler for Google NotebookLM, Claude Projects, and high-context LLMs.

options:
  -h, --help            show this help message and exit
  --config CONFIG, -c CONFIG
                        Path to declarative JSON corpus manifest.
  --repo REPO, -r REPO  Root path of target repository (defaults to current working directory).
  --output-dir OUTPUT_DIR, -o OUTPUT_DIR
                        Destination directory for bundled Markdown volumes (defaults to dist_rag/).
  --auto, -a            Auto-discover repository architecture and generate volumes automatically.
  --emit-config EMIT_CONFIG
                        Emit auto-discovered configuration to specified JSON path and exit.
  --single-file         Also write a single monolithic Markdown file containing all volumes concatenated.
  --check               Dry run: inspect files and compute word counts without writing output.
  --version, -v         show program's version number and exit
```

---

## Contributing & Testing

Run unit tests with `pytest`:
```bash
pytest tests
```

---

## License

MIT License. Copyright (c) 2026 aedmark.
