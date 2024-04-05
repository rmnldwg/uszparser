#!/usr/bin/env python

import re
from datetime import timedelta
from typing import Any, Literal
import warnings

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
    def func(raw, *_a, **_kw):
        try:
            return choices[raw]
        except KeyError:
            return None

    return func


def discard_char(value, *_args, **_kwargs):
    """Raises an exception if there are two numbers. E.g. in 'N01'."""
    if isinstance(value, (int, float)):
        return int(value)

    findings = re.findall("[0-9]|x", value)
    if len(findings) != 1:
        raise ValueError(
            f"string should only contain ONE number, but found {len(findings)}"
        )

    res = findings[0]
    if res == 'x':
        res = 2

    return int(res)


def age(diagnose_n_birth, *_args, **_kwargs):
    """Compute age from array with two entries: Date of birth & date of
    diagnosis."""
    birth = dtprs.parse(diagnose_n_birth[0], dayfirst=True)
    diag = dtprs.parse(diagnose_n_birth[1], dayfirst=True)

    age = diag.year - birth.year

    if ((diag.month < birth.month)
            or (diag.month == birth.month and diag.day < birth.day)):
        age -= 1

    return age


def find(arr, *_args, icd_code=False, **_kwargs):
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


def reformat_date(value, *_args, rand_days_offset: int = 0, **_kwargs):
    """Bring dates into uniform format."""
    value = str(value)
    try:
        diagnose_date = dtprs.parse(value, dayfirst=True)
    except dtprs.ParserError:
        return None

    rand_offset = timedelta(days=rand_days_offset)
    offset_diagnose_date = diagnose_date + rand_offset
    return offset_diagnose_date.strftime("%Y-%m-%d")


def compute_hash(*args, **_kwargs):
    """Compute a hash vlaue from all given arguments."""
    return hash(args)


FUNC_DICT = {
    "discard_char": discard_char,
    "find_subsite": find,
    "find_icd": lambda x, *_a, **_kw: find(x, icd_code=True),
    "date": reformat_date,
    "age": age,
    "str": lambda x, *_a, **_kw: str(x).lower(),
    "int": lambda x, *_a, **_kw: int(x),
    "float": lambda x, *_a, **_kw: float(x),
    "bool": lambda x, *_a, **_kw: bool(x),
    "hash": compute_hash,
    "keep": lambda *args, **_kw: args[0],
    "nothing": lambda *_a, **_kw: None
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


def flatten_recursively(
    nested: dict[str, Any],
    redux_dict: dict[tuple[str], dict[str, Any]] | None = None,
    current_branch: tuple[str] = (),
) -> list[tuple[str]]:
    """Recursively traverse a nested dict and flatten it."""
    redux_dict = redux_dict or {}

    if "row" in nested:
        redux_dict[current_branch] = nested
        return redux_dict
    else:
        for key, item in nested.items():
            new_branch = (*current_branch, key)
            redux_dict = flatten_recursively(item, redux_dict, new_branch)

        return redux_dict


def warning_from_execption(exc):
    """Convert an exception to a warning.

    Taken from https://stackoverflow.com/a/77868794
    """
    warning = RuntimeWarning(*exc.args)
    warning.with_traceback(exc.__traceback__)
    return warning


def parse_sheet(
    sheet,
    mapping,
    offset: int = 0,
    handling: Literal["raise", "warn", "ignore"] = "warn",
):
    """Parse one Excel sheet according to the mapping instructions."""
    new_row = {}

    for column, instr in mapping.items():
        row, col = instr["row"], instr["col"]
        try:
            raw = sheet.iloc[row, col].values
        except AttributeError:
            raw = sheet.iloc[row, col]
        except ValueError:
            raw = None

        try:
            func = func_from(instr["choices"])
        except KeyError:
            func = FUNC_DICT[instr["func"]]

        try:
            new_row[column] = func(raw, rand_days_offset=offset)
        except Exception as exc:
            id = sheet.iloc[1,1]
            msg = f"error in cell(s) [{col},{row}] (should be mapped to {column}) of patient {id}:"
            if handling == "raise":
                raise Exception(msg) from exc
            if handling == "warn":
                print(msg)
                warnings.warn(warning_from_execption(exc))
            new_row[column] = None

    return new_row


def parse_file(
    excel_sheets: dict[Any, pd.DataFrame],
    mapping: dict[str, Any],
    anonymise_date: bool = True,
    seed: int | None = None,
    verbose: bool = False,
    fail_quickly: bool = True,
) -> pd.DataFrame:
    """Parse sheets of an excel file according to instructions in `mapping`."""
    mapping = flatten_recursively(mapping)
    column_headers = mapping.keys()
    header_lengths = [len(tuple) for tuple in column_headers]

    if len(set(header_lengths)) > 1:
        raise ValueError(
            "Depth of provided JSON file is inconsistent. All entries must be located "
            "at the same depth."
        )

    multi_index = pd.MultiIndex.from_tuples(tuples=column_headers)
    data_frame = pd.DataFrame(columns=multi_index)

    handling = "raise" if fail_quickly else "ignore"
    if verbose:
        sheets = tqdm(
            excel_sheets.items(),
            desc="Looping through sheets",
            ncols=100
        )
        handling = "warn"
    else:
        sheets = excel_sheets.items()

    if anonymise_date:
        rng = default_rng(seed)
        base_offset = rng.integers(low=-90, high=90)

    for _name, sheet in sheets:
        if anonymise_date:
            patient_offset = int(base_offset + rng.integers(low=-30, high=30))
        else:
            patient_offset = 0

        new_row = parse_sheet(sheet, mapping, offset=patient_offset, handling=handling)
        data_frame.loc[len(data_frame)] = new_row

    return data_frame
