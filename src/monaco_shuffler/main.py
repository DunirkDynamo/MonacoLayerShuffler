"""Application entry point.

The entry point creates the Qt application object and hands control to the GUI
class. Keeping this file small makes packaging into an executable straightforward.
"""

from argparse import ArgumentParser
import sys

from PySide6.QtWidgets import QApplication

from monaco_shuffler import __version__
from monaco_shuffler.gui import MonacoShufflerApp


def main(argv=None) -> None:
    """Launch the Monaco Shuffler GUI.

    Args:
        argv: Optional argument list for testing or embedding.
    """

    parser = ArgumentParser(description="Preview Monaco layer reorderings.")
    parser.add_argument(
        "--version",
        action="version",
        version=f"monaco-shuffler {__version__}",
    )
    parser.parse_args(argv)

    qt_args = sys.argv if argv is None else [sys.argv[0]] + list(argv)
    app = QApplication(qt_args)
    app.setApplicationVersion(__version__)

    window = MonacoShufflerApp(initial_records=[], source_path=None)

    window.show()
    app.exec()


if __name__ == "__main__":
    main()