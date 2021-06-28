#!/usr/bin/env python

import argparse as ap
from pathlib import Path

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
    print("Open files (Excel & JSON)... ", end="")

# open JSON file & create tuple, MultiIndex
json_file = open(args.json, 'r')
# open excel
kisim_numbers = pd.read_excel(args.excel,
                                usecols='A',
                                dtype={"KISIM": str})["KISIM"].to_list()
excel_data = pd.read_excel(args.excel,
                            sheet_name=kisim_numbers,
                            header=None)

# be verbose
if args.verbose:
    print("DONE")
    
# parse
new_data = parse(excel_data, kisim_numbers, json_file, verbose=args.verbose)

# save
new_data.to_csv(args.save, index=False)