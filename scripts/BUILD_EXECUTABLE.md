# Build the executable locally

This folder contains the local build script for users who want to package their own copy of Monaco Shuffler after making edits.

## Where the script lives

The script is located at:

- `scripts/build-executable.ps1`

Run it from PowerShell in the repository root, or call it with an absolute path.

## What the script does

The script:

- installs the build dependencies defined by the project
- builds the executable with PyInstaller
- writes the finished app to `dist/MonacoShuffler.exe`

## How to use it

From the repository root:

```powershell
.\scripts\build-executable.ps1
```

If you have made source changes and want a fresh executable, rerun the script after saving your edits.

## Build yourself vs. download a release

Use the local build script when you want the executable to match your own code changes. This is the right choice if you have edited the source and want to package your updated version.

Download a GitHub Release when you want a ready-made executable for a tagged version. Releases are produced only from version tags in the form `v*.*.*`, so they are convenient when you do not want to build anything locally.

In short:

- build locally when you changed the code
- download a release when you want the published version for a tag