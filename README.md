# USZ Parser

Program for parsing the Excel files were each instance's data is stored in a separate sheet, instead of a row or column on the same sheet. This way of storing data in an Excel file can be more human-readable, but it makes it harder to parse with things like ``pandas``.


## Installation

To install this program or use the function it provides as a module, start by cloning the repository:

```
git clone https://github.com/rmnldwg/uszparser.git
```

then, ``cd`` into it

```
cd uszparser
```

Now - assuming you have [``venv``](https://docs.python.org/3/library/venv.html) installed (if not you can probably install it with ``sudo apt install python3-venv``) - proceed by creating a virtual environment in which to install all dependencies. This isn't strictly necessary, you could just use ``pip`` (can be installed via ``sudo apt install python3-pip``) to install all packages, but it is good practice to keep everything contained to avoid mess-ups:

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Afterwards you can install the program/package itself via

```
pip install .
```

> [!NOTE]
> To deactivate the virtual environment when you're done using the uszparser, simply run the command ``deactivate``.

## Usage

After the installation you can run the program by typing

```
python -m uszparser
```

Add the flag ``--help`` to show the help text for the correct use of its arguments, which I will explain in the next section, which should look like this:

```
usage: uszparser [-h] [-j JSON] [-s SAVE] [-t] [-o] [--seed SEED] [-v] [-f] excel

Program for parsing the excel file that was created by Bertrand Pouymayou. The excel file's particular structure makes it necessary to hard-code the location of all information. It is stored in the accompanying JSON file.

positional arguments:
  excel                 Excel file that is supposed to be parsed

options:
  -h, --help            show this help message and exit
  -j JSON, --json JSON  JSON file that contains what to parse
  -s SAVE, --save SAVE  Where to save the resulting CSV file? (Default: './parsed.csv')
  -t, --transform       Transform left/right to ipsi/contra based on primary tumor.
  -o, --offset          Offset all dates by a random amount of days (same within a patient)
  --seed SEED           Seed value for random offset of dates.
  -v, --verbose         Give progress update
  -f, --fail-quickly    Fail on first parser error.
```

> [!TIP]
> When you provide the additional flag `-v`, you will also get informed in which patients and which cells the parsing failed.

### Excel file structure

The Excel sheets can have any structure, as long as each sheet has the same layout. Also, right now it is necessary that the first sheet contains - in the first column with header ``KISIM`` - a list with the names of all sheets that are supposed to be read in. I will change this in the future, though, to be more flexible.


### JSON settings

Where on each sheet to find which information is stored in a JSON file. A simple example would look like this:

```json
{
    "patient": {
        "row": 1,
        "col": 1,
        "func": "str"
    },
    "age": {
        "row": [3,4],
        "col": 1,
        "func": "age"
    },
    "HPV status": {
        "row": 29,
        "col": 1,
        "choices": {
            "positive": true,
            "negative": false
        }
    }
}
```

This would yield the following CSV table:

| patient |  age | HPV status |
| :------ | ---: | :--------- |
| Dieter  |   57 | TRUE       |
| Clara   |   27 | FALSE      |
| ...     |  ... | ...        |

As you can see, each key in the JSON file corresponds to the name of a row. For each of those columns the JSON file provides the row number ``row`` and column number ``col`` of the information is refers to. Lastly, there is always either a ``func`` given or a set of ``choices``. In the latter case the program searches for the keys (here ``positive`` and ``negative``) and maps them to the values (``true`` and ``false``). If a function name is given through ``func``, then the program takes whatever it finds at the indicated position and passes it to the specified function ``func``. Currently, the program understands the following functions:

| function         | description                                                                                  |
| :--------------- | :------------------------------------------------------------------------------------------- |
| ``nothing``      | do nothing                                                                                   |
| ``str``          | interpret as lowercase string                                                                |
| ``int``          | interpret as integer                                                                         |
| ``float``        | interpret as decimal number                                                                  |
| ``bool``         | interpret as boolean                                                                         |
| ``date``         | convert string in the format of YYYY-MM-DD into a date object                                |
| ``discard_char`` | convert e.g. "T2" to ``2`` by discarding the first character                                 |
| ``age``          | compute the patient's age from birthday and diagnose date (both locations must be specified) |
| ``find_subsite`` | find subsite in array                                                                        |
| ``find_icd``     | find ICD code in array                                                                       |

In the example above, I have used the ``func``tion ``age`` to compute the patient's age from two values at ``[3,1]`` and at ``[4,1]``.

#### Multi-Header ``(pandas.MultiIndex)``

If you want to extract many columns per instance/sheet it might be difficult to come up with unique non-conflicting column names. For that purpose you can use multi-row headers by simply making the dictionary in the JSON file deeper:

```json
{
    "patient": {
        "name": {
            "row": 1,
            "col": 1,
            "func": "str"
        },
        "gender": {
            "row": 2,
            "col": 1,
            "func": "str"
        },
        "age": {
            "row": [3,4],
            "col": 1,
            "func": "age"
        },
    },
    "condition": {
        "HPV status": {
            "row": 29,
            "col": 1,
            "choices": {
                "positive": true,
                "negative": false
            }
        },
        "T-stage": {
            "row": 25,
            "col": 1,
            "func": "discard_char"
        }
    }
}
```

This JSON file would then give the following CSV table:

| patient<br>name | patient<br>gender | patient<br>age | condition<br>HPV status | condition<br>T-stage |
| :-------------- | :---------------- | -------------: | :---------------------- | :------------------- |
| Dieter          | male              |             57 | TRUE                    | 3                    |
| Clara           | female            |             27 | FALSE                   | 1                    |
| ...             | ...               |            ... | ...                     | ...                  |

> [!NOTE]
> The depth of the JSON dictionary must be the same for all entries. So, if you have decided on how many rows you want for the CSV table, you must structure the entire JSON file accordingly.
