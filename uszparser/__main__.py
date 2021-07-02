#!/usr/bin/env python

import argparse as ap
from pathlib import Path
import pandas as pd
import json

# import and configure icecream
from icecream import ic
ic.configureOutput(prefix="", outputFunction=print)

from .uszparser import parse


# ARGPARSE: parse command line arguments. Namely the path to the excel 
# file, the json file that stores the details of every entry of interest, as 
# well as the path to the location where the final csv is supposed to be 
# stored.
parser = ap.ArgumentParser(description=__doc__)
parser.add_argument("excel", 
                    help="Excel file that is supposed to be parsed")
parser.add_argument("-j", "--json", 
                    default=Path(".").resolve() / "settings.json",
                    help="JSON file that contains what to parse")
parser.add_argument("-s", "--save", 
                    default=Path('.').resolve() / "parsed.csv",
                    help=("Where to save the resulting CSV file? (Default: "
                            "\"./parsed.csv\")"))
parser.add_argument("-v", "--verbose", action="store_true", 
                    help="Give progress update")
args = parser.parse_args()

# be verbose
if args.verbose:
    ic.enable()
else:
    ic.disable()

with open(args.json, 'r') as json_file:
    dictionary = json.load(json_file)
    
ic("Opened JSON file")

first_sheet = pd.read_excel(
    args.excel,
    usecols='A',
    dtype={"KISIM": str}
)
ic("Read KISIM numbers from first sheet of Excel")
kisim_numbers = first_sheet["KISIM"].to_list()
# ...find all the sheets to parse.
excel_data = pd.read_excel(args.excel,
                           sheet_name=kisim_numbers,
                           header=None)
ic("Used KISIM numbers to open sheets")
    
data_frame = parse(excel_data, dictionary, verbose=args.verbose)
ic("Parsing successfully finished!")

data_frame.to_csv(args.save, index=False)
ic("CSV has been saved to disk!")