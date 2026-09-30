# Architecture

This repository is organized as a small Python application with a src-based package layout. The code is split so database lookup, file parsing, preview logic, and the GUI remain separate and easy to extend.

## High-Level Shape

```mermaid
flowchart LR
    A[MRN and plan prompt] --> B[Database lookup]
    B --> C[Text file input]
    C --> D[Core parsing]
    D --> E[Ordered records]
    E --> F[GUI table]
    F --> G[Dropdown selections]
    G --> H[Preview reorder]
    H --> F
    G --> I[File rewrite]
```

## Repository Layout

- [pyproject.toml](pyproject.toml) defines packaging metadata, the console entry point, and the optional build dependency for PyInstaller.
- [README.md](README.md) gives a short project summary and build notes.
- [QUICK_START.md](QUICK_START.md) gives the shortest path to run and package the app.
- [src/monaco_shuffler/__init__.py](src/monaco_shuffler/__init__.py) exposes the package version.
- [src/monaco_shuffler/core.py](src/monaco_shuffler/core.py) contains database lookup, parsing, and reorder-preview rules.
- [src/monaco_shuffler/gui.py](src/monaco_shuffler/gui.py) contains the PySide6 interface and widget wiring.
- [src/monaco_shuffler/main.py](src/monaco_shuffler/main.py) is the application entry point.
- [src/monaco_shuffler/data/sample_layers.txt](src/monaco_shuffler/data/sample_layers.txt) provides bundled sample input.

## Runtime Layers

### 1. Data ingestion

The application first prompts for an MRN and plan name, then resolves the
matching file from the configured database root. The loaded file is a
Monaco-style text file where each structure is stored as two lines:

1. structure name
2. layer index

The parser in [src/monaco_shuffler/core.py](src/monaco_shuffler/core.py) validates that the file contains complete name/index pairs, converts the indices to integers, and sorts the resulting records by original layer.

### 2. Domain logic

[src/monaco_shuffler/core.py](src/monaco_shuffler/core.py) owns the reorder rules:

- parse raw text into structure records
- derive default dropdown values from the original file order
- validate selected target layers
- build the preview order shown in the UI

This module is intentionally UI-agnostic so the file-writing step can reuse the same validation later.

### 3. User interface

[src/monaco_shuffler/gui.py](src/monaco_shuffler/gui.py) builds the desktop window with PySide6.

The GUI currently provides:

- a scrollable table of structures
- the original layer number column
- a dropdown for choosing a target layer
- a preview column that shows the reordered result after confirmation
- a reset button that restores default values
- an Apply Reorder button placeholder for the future write-back step

### 4. Application startup

[src/monaco_shuffler/main.py](src/monaco_shuffler/main.py) starts the Qt application and launches the initial MRN/plan prompt flow.

Startup order:

1. launch the Qt application
2. prompt for an 8-digit MRN
3. resolve the MRN folder under the configured database root
4. prompt for a plan name
5. resolve the matching plan subfolder and load the `plan` file inside it
6. launch the main window with the loaded records

## Current Behavior

The repo currently supports previewing reorderings and writing the reordered
plan back to the loaded file.

## Packaging Model

The project uses a standard Python package layout under `src/` so it can be:

- run from source during development
- installed as an editable package
- built into a Windows executable with PyInstaller

The console entry point is `monaco-shuffler`, mapped to [src/monaco_shuffler/main.py](src/monaco_shuffler/main.py).

## Extension Points

The main future addition is extending the database lookup and save pipeline. When that is implemented, the same architecture should hold:

- keep Monaco file parsing in `core.py`
- keep file mutation logic in a second core service, not in the GUI
- let the GUI only collect user choices and display preview state

That separation will make it easier to support multiple Monaco file formats or additional validation rules without reworking the window code.