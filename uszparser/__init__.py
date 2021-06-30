"""Program for parsing the excel file that was created by Bertrand Pouymayou 
and then filled with patients by Jean-Marc Hoffmann. The excel file's 
particular structure makes it necessary to hard-code the location of all 
information. It is stored in the accompanying JSON file."""

__author__ = "Roman Ludwig"
__license__ = "MIT"
__email__ = "roman.ludwig@usz.ch"
__uri__ = "https://lymph-model.readthedocs.io"

__all__ = [
    "multiIndex_from_json",
    "parse",
]

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions