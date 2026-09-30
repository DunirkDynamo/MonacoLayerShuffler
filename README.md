# Monaco Shuffler

Monaco Shuffler is a small Python desktop app for previewing and saving reordered layer indices from Monaco-style text files.

## What it does

This app focuses on a simple, explicit workflow:

- finds the structure list inside a larger text file
- validates the candidate list before loading it
- shows each structure with its current layer index and CSV payload
- lets you choose a new destination index for each structure
- previews the reordered result before saving
- writes the edited file and also keeps an `_OG` backup copy of the original input

## Versioning

The package version is now derived from git tags using `setuptools-scm`.

For a release, create and push a tag like `v0.1.1`.
Only tags in the form `v*.*.*` are treated as release versions:

```bash
git tag -a v0.1.1 -m "Release v0.1.1"
git push --tags
```

When you install or build from that tagged source, the package version will be generated automatically.
Pushing a matching release tag also updates the GitHub Pages site and publishes the Windows executable release.

## Release automation

When a tag in the form `v*.*.*` is pushed, GitHub Actions will:

- update the GitHub Pages site for that release tag
- build the Windows executable with PyInstaller
- publish a GitHub Release with the executable attached

## Project layout

- `src/monaco_shuffler/core.py` holds parsing and reorder logic
- `src/monaco_shuffler/gui.py` holds the PySide6 interface
- `src/monaco_shuffler/main.py` is the entry point
- `src/monaco_shuffler/data/sample_layers.txt` is a bundled sample file

## Run from source

If you have already installed the package in editable mode (`pip install -e .`),
you can launch the app with:

```bash
python -m monaco_shuffler.main
```

If you want to open a specific file:

```bash
python -m monaco_shuffler.main --file PretendData.txt
```

If the file path is wrong or the file does not exist, the app stops and shows an error instead of loading sample data.

To print the current tagged version from the command line:

```bash
python -m monaco_shuffler.main --version
```

## Build an executable

Install the build extra first:

```bash
pip install -e .[build]
```

Then build a Windows executable with PyInstaller:

```bash
pyinstaller --noconfirm --onefile --windowed --name MonacoShuffler -m monaco_shuffler.main
```

The finished executable will be created under `dist/`.
For tagged releases, the same executable is built automatically in GitHub Actions and attached to the GitHub Release.

For a local build script that installs the build dependencies and runs PyInstaller for you, see [scripts/BUILD_EXECUTABLE.md](scripts/BUILD_EXECUTABLE.md).