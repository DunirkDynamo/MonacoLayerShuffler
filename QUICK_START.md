# Quick Start

Monaco Shuffler is a small desktop app for previewing Monaco-style layer reorders.

## 1. Install Python

Install Python 3.9 or newer from [python.org](https://www.python.org/downloads/).

When installing on Windows, make sure the installer adds Python to your PATH.

This project uses PySide6 for the GUI, so the package install step will bring in the Qt runtime automatically.

## 2. Get the project

If you already have the repository folder, open it in your editor and skip this step.

Otherwise, clone the repo and enter the folder:

```bash
git clone <your-repo-url>
cd "Monaco Shuffler"
```

## 3. Create a virtual environment

From the project folder, create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

If activation succeeds, your terminal prompt should show `(.venv)`.

## 4. Install the app

Install the project in editable mode so local changes are picked up immediately:

```bash
pip install -e .
```

If you want the executable build tools too, install the build extra:

```bash
pip install -e .[build]
```

The package version is generated from git tags through `setuptools-scm`, so if
you are working from a tagged release the version number will match that tag.

## 5. Run the app

If you installed the package in editable mode, launch the GUI with:

```bash
python -m monaco_shuffler.main
```

The app starts empty if you do not pass a file.

You can also open a specific file at startup:

```bash
python -m monaco_shuffler.main --file PretendData.txt
```

If the file path is wrong or the file does not exist, the app will show an error instead of guessing a fallback file.

You can also print the current version:

```bash
python -m monaco_shuffler.main --version
```

## Use the GUI

- Each row shows the original layer number and structure name.
- Use the dropdown beside a structure to choose its new destination layer.
- Click `Confirm Reorder` to preview the reordered result in the rightmost column.
- Click `Reset` to restore every dropdown to its original value.
- `Apply Reorder` is the placeholder for the file-writing step that will come next.

## 6. Build an executable

Then build a Windows executable with PyInstaller:

```bash
pyinstaller --noconfirm --onefile --windowed --name MonacoShuffler -m monaco_shuffler.main
```

The executable will be created in the `dist` folder.

If you want a one-command local build helper, use [scripts/build-executable.ps1](scripts/build-executable.ps1) and read [scripts/BUILD_EXECUTABLE.md](scripts/BUILD_EXECUTABLE.md).

## 7. Tag a release

When you're ready to publish a release, create and push a git tag in the form `v*.*.*`:

```bash
git tag -a v0.1.1 -m "Release v0.1.1"
git push --tags
```

That tag becomes the source of truth for the package version when the app is built or installed.
Pushing the tag updates the GitHub Pages site.
To build and publish the executable, open the repository Actions tab and run the manual release workflow with that tag.