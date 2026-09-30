"""Application entry point.

The entry point resolves an optional file, creates the Qt application object,
and hands control to the GUI class. Keeping this file small makes packaging
into an executable straightforward.
"""

from argparse import ArgumentParser
from pathlib import Path
import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtWidgets import QMessageBox

from monaco_shuffler import __version__
from monaco_shuffler.core import load_structure_file
from monaco_shuffler.gui import MonacoShufflerApp


def main(argv=None) -> None:
    """Launch the Monaco Shuffler GUI.

    Args:
        argv: Optional argument list for testing or embedding.
    """

    parser = ArgumentParser(description="Preview Monaco layer reorderings.")
    parser.add_argument(
        "--file",
        type=Path,
        help="Optional Monaco-style text file to open on startup.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"monaco-shuffler {__version__}",
    )
    args = parser.parse_args(argv)

    qt_args = sys.argv if argv is None else [sys.argv[0]] + list(argv)
    app = QApplication(qt_args)
    app.setApplicationVersion(__version__)

    if args.file is not None:
        if not args.file.exists():
            QMessageBox.critical(
                None,
                "File not found",
                f"The file '{args.file}' does not exist. Please check the path and try again.",
            )
            sys.exit(1)

        document = load_structure_file(args.file)
        window = MonacoShufflerApp(
            initial_records=document.records,
            source_path=args.file,
            initial_document=document,
        )
    else:
        window = MonacoShufflerApp(initial_records=[], source_path=None)

    window.show()
    app.exec()


if __name__ == "__main__":
    main()