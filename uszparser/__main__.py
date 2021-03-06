#!/usr/bin/env python

import argparse as ap
from pathlib import Path
import pandas as pd
import json
import time

from .uszparser import parse, lr2ic, SimpleLog


# ARGPARSE: parse command line arguments. Namely the path to the excel 
# file, the json file that stores the details of every entry of interest, as 
# well as the path to the location where the final csv is supposed to be 
# stored.
parser = ap.ArgumentParser(description=__doc__)
parser.add_argument(
    "excel", 
    help="Excel file that is supposed to be parsed"
)
parser.add_argument(
    "-j", "--json", 
    default=Path(".").resolve() / "settings.json",
    help="JSON file that contains what to parse"
)
parser.add_argument(
    "-s", "--save", 
    default=Path('.').resolve() / "parsed.csv",
    help="Where to save the resulting CSV file? (Default: './parsed.csv')"
)
parser.add_argument(
    "-t", "--transform", 
    action="store_true", 
    help="Transform left/right to ipsi/contra based on primary tumor."
)
parser.add_argument(
    "-o", "--offset",
    action="store_true",
    help="Offset all dates by a random amount of days (same within a patient)"
)
parser.add_argument(
    "--seed",
    default=None, type=int,
    help="Seed value for random offset of dates."
)
parser.add_argument(
    "-v", "--verbose", 
    action="store_true", 
    help="Give progress update"
)
args = parser.parse_args()

# be verbose
sl = SimpleLog(enabled=args.verbose)

# keep time
start = time.time()

sl.log("Opening JSON specification file...", end="")
with open(args.json, 'r') as json_file:
    dictionary = json.load(json_file)
sl.log("DONE")

sl.log("Extracting sheet names from first sheet...", end="")
first_sheet = pd.read_excel(
    args.excel,
    usecols='A',
    dtype={"KISIM": str}
)
kisim_numbers = first_sheet["KISIM"].to_list()
sl.log("DONE")

sl.log(f"Reading in all {len(kisim_numbers)} specified sheets...", end="")
excel_data = pd.read_excel(args.excel,
                           sheet_name=kisim_numbers,
                           header=None)
sl.log("DONE")

sl.log("Parsing loaded sheets according to JSON specs...", end="")
data_frame = parse(
    excel_data, dictionary, 
    offset_date=args.offset, 
    seed=args.seed, 
    verbose=args.verbose
)
sl.log("DONE")

if args.transform:
    sl.log("Transform left/right to ipsi/contra...", end="")
    data_frame = lr2ic(data_frame)
    sl.log("DONE")

sl.log("Saving resulting CSV to disk...", end="")
data_frame.to_csv(args.save, index=False)
sl.log("DONE")

end = time.time()
sl.log(f"Finished after {end - start:.2f} seconds")