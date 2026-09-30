"""Monaco Shuffler package.

This package contains the parsing, reorder preview, and GUI entry points for
the Monaco layer reordering tool.
"""

__all__ = ["__version__"]

try:
	from ._version import version as __version__
except ImportError:
	try:
		from importlib.metadata import PackageNotFoundError, version as _package_version
	except ImportError:
		__version__ = "0.0.0"
	else:
		try:
			__version__ = _package_version("monaco-shuffler")
		except PackageNotFoundError:
			__version__ = "0.0.0"