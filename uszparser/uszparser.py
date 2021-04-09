#!/usr/bin/env python

import pandas as pd 
import numpy as np 
from dateutil import parser as dtprs
from pathlib import Path
import argparse as ap 
from itertools import product
import json
import re



def yn2tf(yesno):
    """Function that converts 'yes' & 'no' into `True` & `False`."""
    try:
        if yesno.casefold() == "yes":
            return True
        elif yesno.casefold() == "no":
            return False
        else:
            return None
    except:
        return None



def posneg2tf(posneg):
    """Function that converts 'positive' & 'negative' into `True` & `False`."""
    try:
        if posneg.casefold() == "positive":
            return True
        elif posneg.casefold() == "negative":
            return False
        else:
            return None
    except:
        return None



def discard_char(string):
    """Raises an exception if there are two numbers. E.g. in 'N01'."""
    findings = re.findall("[0-9]|x", string)
    if len(findings) != 1:
        raise Exception(
            f"string should only contain ONE number, but found {len(findings)}")

    res = findings[0]
    if res == 'x':
        res = 2  # this is only the case for the M-stage

    return res



def involvement(string):
    if string.casefold() == "unknown":
        return None
    else:
        return yn2tf(string)



def age(diagnose_n_birth):
    """Compute age from array with two entries: Date of birth & date of 
    diagnosis."""
    birth = dtprs.parse(diagnose_n_birth[0])
    diag = dtprs.parse(diagnose_n_birth[1])
    
    age = diag.year - birth.year

    if ((diag.month < birth.month)
            or (diag.month == birth.month and diag.day < birth.day)):
        age -= 1

    return age



def find(arr, icd_code=False):
    """Search in the first column of `arr` for a 'Yes' and return the respective 
    entry in the second column."""
    search = [str(item) for item in arr[:,0]]
    find = [str(item) for item in arr[:,1]]
    
    try:
        idx = [i for i,item in enumerate(search) if "Yes" in item]
        found = find[idx[0]]
    except:
        found = "unkown"
    
    if icd_code:
        found = found.replace("\xa0", "")
        found = found.replace(" ", "")
    else:
        found = found.lower()
        
    return found



def multiIndex_from_json(json_file):
    """Create pandas MultiIndex with three layers from the set-up .json file."""
    json_dict = json.load(json_file)
    
    # tuples for MultiIndex
    idx_tuples = []
    
    # tuples for general patient info
    for lvl2 in json_dict["patient"]:
        for lvl3 in json_dict["patient"][lvl2]:
            idx_tuples.append(("patient", lvl2, lvl3))
            
    # tuples for tumor info
    for lvl3 in json_dict["tumor"]["1"]:
        idx_tuples.append(("tumor", "1", lvl3))
    
    # tuples for involvement info
    modalities = json_dict["modalities"]
    sides = list(json_dict["modalities_cols"].keys())
    lnls = json_dict["lnls"]
    
    for mod in modalities:
        idx_tuples.append((mod, "info", "date"))
        idx_tuples += list(product([mod], sides, lnls))
    
    # return MultiIndex from tuples
    return idx_tuples, pd.MultiIndex.from_tuples(idx_tuples), json_dict



def parse(excel_data: pd.DataFrame, 
          kisim_numbers: list, 
          json_file,
          verbose:bool =False) -> pd.DataFrame:
    """Parse an excel dataset according to instructions in a JSON file.
    
    Args:
        excel_data: Excel file as read in by pandas
        kisim_numbers: list of KISIM numbers of the patients. They can be found 
            on the first sheet of the Excel file and also on every sheet (which 
            corresponds to one patient).
        json_file: The opened JSON file that contains info on where to find 
            which entry.
        verbose: If `True`, print progress of parsing.
        
    Returns:
        The parsed data."""
    # list of functions that are supposed to be called for the 'func' keywords
    # in the JSON file
    func_dict = {"yn2tf": yn2tf,
                 "posneg2tf": posneg2tf,
                 "discard_char": discard_char,
                 "find_subsite": find,
                 "find_icd": lambda x: find(x, icd_code=True),
                 "date": lambda x: dtprs.parse(x).date().strftime("%Y-%m-%d"),
                 "age": age,
                 "str": lambda x: str(x).lower(),
                 "int": int,
                 "float": float,
                 "bool": bool,
                 "inv": involvement,
                 "nothing": lambda *args: args[0]}
    
    # be verbose
    if verbose:
        print("Create MultiIndex & parse JSON file... ", end="")
    
    # create the MultiIndex & convert JSON file to dictionary
    idx_tuples, multi_idx, json_dict = multiIndex_from_json(json_file)

    # be verbose
    if verbose:
        print("DONE")
        print("Create DataFrame... ", end="")

    # new DataFrame where all the information will be stored
    new_data = pd.DataFrame(columns=multi_idx)

    # be verbose
    if verbose:
        print("DONE")

    # loop through sheets
    for i, (kisim, sheet) in enumerate(excel_data.items()):
        # make sure the KISIM number exists and matches with the list of patients
        if (int(kisim) != sheet.iloc[1, 1]) or (kisim != kisim_numbers[i]):
            raise Exception("KISIM numbers don't match")

        # append new row to pandas DataFrame
        new_row = {}

        # add patient info to new row
        item1 = json_dict["patient"]
        for key2, item2 in item1.items():
            for key3, item3 in item2.items():
                try:
                    raw = sheet.iloc[item3["row_loc"], item3["col_loc"]].values
                except AttributeError:
                    raw = sheet.iloc[item3["row_loc"], item3["col_loc"]]
                except ValueError:
                    raw = None

                func = func_dict[item3["func"]]
                new_row[("patient", key2, key3)] = func(raw)

        # add tumor info to new row
        item1 = json_dict["tumor"]
        for key2, item2 in item1.items():
            for key3, item3 in item2.items():
                try:
                    raw = sheet.iloc[item3["row_loc"], item3["col_loc"]].values
                except AttributeError:
                    raw = sheet.iloc[item3["row_loc"], item3["col_loc"]]
                except ValueError:
                    raw = None

                func = func_dict[item3["func"]]
                new_row[("tumor", key2, key3)] = func(raw)

        # add involvement info to new row
        modalities = json_dict["modalities"]
        mod_rows = json_dict["modalities_rows"]
        mod_info_row = json_dict["modalities_info_row"]
        mod_info_cols = json_dict["modalities_info_cols"]

        sides = list(json_dict["modalities_cols"].keys())

        lnls = json_dict["lnls"]
        l_rows = json_dict["lnls_rows"]

        for i, mod in enumerate(modalities):
            try:
                date_str = sheet.iloc[mod_info_row, mod_info_cols[i]]
                date_str = date_str.split()[0]
                new_row[(mod, "info", "date")] = func_dict["date"](date_str)
            except:
                new_row[(mod, "info", "date")] = None

            for j, s in enumerate(sides):
                s_cols = json_dict["modalities_cols"][s]
                for k, l in enumerate(lnls):
                    row = mod_rows[i] + l_rows[k]
                    col = s_cols[i]
                    new_row[(mod, s, l)] = func_dict["inv"](
                        sheet.iloc[row, col])

        # add new row to the DataFrame
        new_data = new_data.append(new_row, ignore_index=True)

        # be verbose
        if verbose:
            print(
                f"\rLooping through sheets...{100 * (i+1) / len(kisim_numbers):6.2f}%", end="")

    # be verbose
    if verbose:
        print("\033[2K", end="")
        print("\rLooping through sheets... DONE")

    # return created DataFrame
    return new_data



if __name__ == "__main__":
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
