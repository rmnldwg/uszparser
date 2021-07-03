#!/usr/bin/env python

import pandas as pd
from dateutil import parser as dtprs

import re
from typing import Dict, Tuple, List, Any, Optional

from tqdm import tqdm


class SimpleLog(object):
    """Very basic class for verbose output inspired by `icecream`."""
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        
    def log(self, string, **kwargs):
        if self.enabled:
            print(string, **kwargs)


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
        res = 2

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


def reformat_date(string):
    """Bring dates into uniform format."""
    string = string.split()[0]
    dt = dtprs.parse(string)
    return dt.strftime("%Y-%m-%d")


FUNC_DICT = {
    "discard_char": discard_char,
    "find_subsite": find,
    "find_icd": lambda x: find(x, icd_code=True),
    "date": reformat_date,
    "age": age,
    "str": lambda x: str(x).lower(),
    "int": int,
    "float": float,
    "bool": bool,
    "nothing": lambda *args: args[0]
}


def recursive_traverse(dictionary: Dict[str, Any],
                       redux_dict: Dict[Tuple[str], Dict[str, Any]] = {},
                       current_branch: Tuple[str] = ()) -> List[Tuple[str]]:
    """Recursively traverse an arbitrarily deep dictionary and compress its 
    depth.
    """
    if "row" in dictionary:
        redux_dict[current_branch] = dictionary
        return redux_dict
    else:
        for key, item in dictionary.items():
            new_branch = (*current_branch, key)
            redux_dict = recursive_traverse(item, redux_dict, new_branch)

        return redux_dict


def parse(excel_sheets: Dict[Any, pd.DataFrame], 
          dictionary: Dict[str, Any],
          verbose: bool = False) -> pd.DataFrame:
    """Parse sheets of an excel file according to instructions in `dictionary`.
    """
    redux_dict = recursive_traverse(dictionary)
    
    column_tuples = redux_dict.keys()
    tuple_lengths = [len(tuple) for tuple in column_tuples]
    
    if len(set(tuple_lengths)) > 1:
        raise ValueError("Depth of provided JSON file is inconsistent. All "
                         "entries must be located at the same depth.")
    
    multi_index = pd.MultiIndex.from_tuples(tuples=column_tuples)
    data_frame = pd.DataFrame(columns=multi_index)
    
    if verbose:
        sheets = tqdm(
            excel_sheets.items(),
            desc="Looping through sheets",
            ncols=100
        )
    else:
        sheets = excel_sheets.items()
    
    for sheet_name, sheet in sheets:
        new_row = {}

        for column, instr in redux_dict.items():
            try:
                raw = sheet.iloc[instr["row"], instr["col"]].values
            except AttributeError:
                raw = sheet.iloc[instr["row"], instr["col"]]
            except ValueError:
                raw = None
                
            try:
                func = map_with_dict(instr["choices"])
            except KeyError:
                func = FUNC_DICT[instr["func"]]
                
            try:
                new_row[column] = func(raw)
            except:
                new_row[column] = None
            
        data_frame = data_frame.append(new_row, ignore_index=True)
        
    return data_frame
