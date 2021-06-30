#!/usr/bin/env python


import pandas as pd
import numpy as np
from dateutil import parser as dtprs

from itertools import product
import json
import re

# import tqdm & icecream
from tqdm import tqdm
from icecream import ic
ic.configureOutput(prefix="", outputFunction=print)


def map_with_dict(options_dict):
    """Return a function that maps a given input according to the given 
    dictionary to the respective outputs."""
    
    def func(raw):
        try:
            return options_dict[f"{raw}".lower()]
        except KeyError:
            return None
        
    return func



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
          verbose:bool = False) -> pd.DataFrame:
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
    func_dict = {"discard_char": discard_char,
                 "find_subsite": find,
                 "find_icd": lambda x: find(x, icd_code=True),
                 "date": lambda x: dtprs.parse(x).date().strftime("%Y-%m-%d"),
                 "age": age,
                 "str": lambda x: str(x).lower(),
                 "int": int,
                 "float": float,
                 "bool": bool,
                 "nothing": lambda *args: args[0]}
    
    # be verbose
    if verbose:
        ic.enable()
    else:
        ic.disable()
    
    _, multi_idx, json_dict = multiIndex_from_json(json_file)
    ic("Created MultiIndex according to provided JSON file")

    # new DataFrame where all the information will be stored
    new_data = pd.DataFrame(columns=multi_idx)

    # create iterator with progress bar (if verbose)
    if verbose:
        enumerated_sheets = tqdm(
            enumerate(excel_data.items()),
            desc="Looping through sheets: "
        )
    else:
        enumerated_sheets = enumerate(excel_data.items())
    
    # loop through sheets
    for i, (kisim, sheet) in enumerated_sheets:
        # make sure the KISIM number exists and matches with the list of patients
        if (int(kisim) != sheet.iloc[1, 1]) or (kisim != kisim_numbers[i]):
            raise Exception("KISIM numbers don't match")

        # append new row to pandas DataFrame
        new_row = {}

        # add info about patient & tumor to new row
        for sup_category in ["patient", "tumor"]:
            obj = json_dict[sup_category]
            for category, columns in obj.items():
                for column, details in columns.items():
                    try:
                        raw = sheet.iloc[details["row"], details["col"]].values
                    except AttributeError:
                        raw = sheet.iloc[details["row"], details["col"]]
                    except ValueError:
                        raw = None

                    try:
                        func = map_with_dict(details["options"])
                    except KeyError:
                        func = func_dict[details["func"]]
                    
                    new_row[(sup_category, category, column)] = func(raw)

        # add involvement info to new row
        modalities = json_dict["modalities"]
        mod_rows = json_dict["modalities_rows"]
        mod_info_row = json_dict["modalities_info_row"]
        mod_info_cols = json_dict["modalities_info_cols"]

        sides = list(json_dict["modalities_cols"].keys())
        options_dict = {
            "unknown": None,
            "yes": True,
            "no": False
        }
        func = map_with_dict(options_dict)

        lnls = json_dict["lnls"]
        l_rows = json_dict["lnls_rows"]

        for i, mod in enumerate(modalities):
            try:
                date_str = sheet.iloc[mod_info_row, mod_info_cols[i]]
                date_str = date_str.split()[0]
                new_row[(mod, "info", "date")] = func_dict["date"](date_str)
            except:
                new_row[(mod, "info", "date")] = None

            for s in sides:
                s_cols = json_dict["modalities_cols"][s]
                for k, l in enumerate(lnls):
                    row = mod_rows[i] + l_rows[k]
                    col = s_cols[i]
                    new_row[(mod, s, l)] = func(sheet.iloc[row, col])

        # add new row to the DataFrame
        new_data = new_data.append(new_row, ignore_index=True)

    ic("Parsing done")

    # return created DataFrame
    return new_data
