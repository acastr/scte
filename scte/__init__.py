from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("scte")
except PackageNotFoundError:  # not installed (e.g. running from a source tree)
    __version__ = "0.0.0+unknown"

from scte import Scte35
from scte import Scte104
