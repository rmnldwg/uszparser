#!/usr/bin/env python

import re
from datetime import timedelta
from typing import Any

import pandas as pd
from dateutil import parser as dtprs
from numpy.random import default_rng
from tqdm import tqdm


class SimpleLog:
    """Very basic class for verbose output inspired by `icecream`."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled

    def log(self, string, **kwargs):
        if self.enabled:
            print(string, **kwargs)


def func_from(choices):
    """Return a function that maps a given input according to the given
    dictionary to the respective outputs.
    """
    def func(raw):
        try:
            return choices[raw]
        except KeyError:
            return None

    return func


def discard_char(string):
    """Raises an exception if there are two numbers. E.g. in 'N01'."""
    findings = re.findall("[0-9]|x", string)
    if len(findings) != 1:
        raise ValueError(
            f"string should only contain ONE number, but found {len(findings)}"
        )

    res = findings[0]
    if res == 'x':
        res = 2

    return res


def age(diagnose_n_birth):
    """Compute age from array with two entries: Date of birth & date of
    diagnosis."""
    birth = dtprs.parse(diagnose_n_birth[0], dayfirst=True)
    diag = dtprs.parse(diagnose_n_birth[1], dayfirst=True)

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
        found = "unknown"

    if icd_code:
        found = found.replace("\xa0", "")
        found = found.replace(" ", "")
    else:
        found = found.lower()

    return found


def reformat_date(string, rand_days_offset: int = 0):
    """Bring dates into uniform format."""
    string = string.split()[0]
    diagnose_date = dtprs.parse(string, dayfirst=True)
    rand_offset = timedelta(days=rand_days_offset)
    offset_diagnose_date = diagnose_date + rand_offset
    return offset_diagnose_date.strftime("%Y-%m-%d")


def compute_hash(*args):
    """Compute a hash vlaue from all given arguments."""
    return hash(args)


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
    "hash": compute_hash,
    "keep": lambda *args: args[0],
    "nothing": lambda *args: None
}


def lr2ic(
    data_frame: pd.DataFrame
):
    """Transform entries on a left-right basis to a ipsi-contra basis."""
    modalities = list(set(data_frame.columns.get_level_values(level=0)))
    modalities.remove("patient")
    modalities.remove("tumor")

    swap = data_frame[("tumor", "1", "side")] == "right"
    no_swap = data_frame[("tumor", "1", "side")] != "right"
    lnls = list(data_frame[(modalities[0], "left")].columns)

    for mod in modalities:
        for lnl in lnls:
            normal_values = data_frame.loc[
                no_swap, [(mod, "left", lnl), (mod, "right", lnl)]
            ].values
            swapped_values = data_frame.loc[
                swap, [(mod, "right", lnl), (mod, "left", lnl)]
            ].values

            data_frame.loc[
                no_swap, [(mod, "left", lnl), (mod, "right", lnl)]
            ] = normal_values
            data_frame.loc[
                swap, [(mod, "left", lnl), (mod, "right", lnl)]
            ] = swapped_values

    data_frame = data_frame.rename(
        {"left": "ipsi", "right": "contra"},
        axis="columns", level=1
    )

    return data_frame


def recursive_traverse(
    dictionary: dict[str, Any],
    redux_dict: dict[tuple[str], dict[str, Any]] | None = None,
    current_branch: tuple[str] = (),
) -> list[tuple[str]]:
    """Recursively traverse an arbitrarily deep dictionary and compress its
    depth.
    """
    redux_dict = redux_dict or {}

    if "row" in dictionary:
        redux_dict[current_branch] = dictionary
        return redux_dict
    else:
        for key, item in dictionary.items():
            new_branch = (*current_branch, key)
            redux_dict = recursive_traverse(item, redux_dict, new_branch)

        return redux_dict


def parse(
    excel_sheets: dict[Any, pd.DataFrame],
    dictionary: dict[str, Any],
    offset_date: bool = True,
    seed: int | None = None,
    verbose: bool = False,
) -> pd.DataFrame:
    """Parse sheets of an excel file according to instructions in `dictionary`.
    """
    redux_dict = recursive_traverse(dictionary)

    column_tuples = redux_dict.keys()
    tuple_lengths = [len(tuple) for tuple in column_tuples]

    if len(set(tuple_lengths)) > 1:
        raise ValueError(
            "Depth of provided JSON file is inconsistent. All entries must be located "
            "at the same depth."
        )

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

    if offset_date:
        rng = default_rng(seed)
        base_offset = rng.integers(low=-90, high=90)

    for _name, sheet in sheets:
        new_row = {}

        if offset_date:
            patient_offset = int(base_offset + rng.integers(low=-30, high=30))
        else:
            patient_offset = 0

        for column, instr in redux_dict.items():
            try:
                raw = sheet.iloc[instr["row"], instr["col"]].values
            except AttributeError:
                raw = sheet.iloc[instr["row"], instr["col"]]
            except ValueError:
                raw = None

            try:
                func = func_from(instr["choices"])
            except KeyError:
                func = FUNC_DICT[instr["func"]]

            try:
                new_row[column] = func(raw, rand_days_offset=patient_offset)
            except TypeError:
                new_row[column] = func(raw)
            except:
                new_row[column] = None

        data_frame.loc[len(data_frame)] = new_row

    return data_frame
