"""Program for parsing the excel file that was created by Bertrand Pouymayou 
and then filled with patients by Jean-Marc Hoffmann. The excel file's 
particular structure makes it necessary to hard-code the location of all 
information. It is stored in the accompanying JSON file."""

__author__ = "Roman Ludwig"
__license__ = "MIT"
__email__ = "roman.ludwig@usz.ch"


from ._version import get_versions
__version__ = get_versions()['version']
del get_versions


from .uszparser import yn2tf, posneg2tf, discard_char, involvement, age, find, multiIndex_from_json, parse