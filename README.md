# USZ Parser

Program for parsing the excel file that was created by Bertrand Pouymayou and then filled with patients by Jean-Marc Hoffmann. The excel file's particular structure makes it necessary to hard-code the location of all information. This information must be stored in a JSON file.


## JSON structure

The structure of this JSON file determines the header and columns of the final CSV output. E.g. if the JSON dictionary has a depth of two (all entries must have the same depth), then you will end up with a table that has two rows. An example:

```json
{
    "patient": {
        "age": {
            "row": [3,4],
            "col": 1,
            "func": "age"
        },
        "gender": {
            "row": 2,
            "col": 1,
            "func": "str"
        }
    },
    "tumor": {
        "midline-extension": {
            "row": 32,
            "col": 2,
            "choices": {
                "positive": true,
                "negative": false
            }
        }
    }
}
```

This JSON document has three entries. Entries are characterized by dictionaries containing the keywords ``row``, ``col`` and either ``func`` or ``choices``. Each entry itself is the value to the key of a high level dictionary.

The resulting CSV file would look something like this:

```
    | patient | patient | tumor             |
    | age     | gender  | midline-extension |
    | ------- | ------- | ----------------- |
1:  |      67 | male    | true              |
2:  |      71 | female  | false             |
3:  |     ... | ...     | ...               |
```

The first header row corresponds to the top-level keys ``patient`` and ``tumor`` under which one finds another dictionary each which's keys represent the second level of the CSV's header.


## Table structure

The header of the CSV file has three rows. This is to group columns into categories and subcategories. In the list below the overarching categories are the first list level, then comes a finer categorization and finally the name and description of the actual row.

1. **``patient``** This contains all info that is patient-specific
   1.  **``general``** Info not necessarily related to his disease
       1.  **``ID``** (``int``) Random ID number.
       2.  **``gender``** (``male`` or ``female``) Gender of the patient.
       3.  **``age``** (``int``) Age at diagnosis.
       4.  **``diagnosedate``** (``date``) Date of diagnosis. 
   
   2.  **``abuse``** Reports on different drug abuses
       1.  **``alcohol``** (``bool``) Alcoholism or not
       2.  **``nicotine``** (``bool``) Smoker or not
   
   3.  **``condition``** More info about patient's health condition.
       1.  **``HPV``** (``bool``) p16 status.
       2.  **``neck-dissection``** (``bool``) whether patient has undergone neck dissection

   4.  **``stage``** N & M part of the TNM staging system. T is not reported here, since it is tumor-specific
       1.  **``N``** (``int``) Stage of nodal involvement.
       2.  **``M``** (``int``) Stage of distant metastases.


2.  **``tumor``** Collects info about primary tumor(s).
    1.  **``1``** Info about first primary tumor.
        1.  **``location``** (``str``) Location of the tumor.
        2.  **``subsite``** (``str``) Subsite, essentially more precise report of tumor location.
        3.  **``ICD-O-3``** (``str``) ICD code of the tumor subsite.
        4.  **``side``** (``left``, ``right`` or ``central``) Lateralization of primary tumor
        5.  **``extension``** (``bool``) Tumor extends over sagittal midline or not
        6.  **``size``** (``float``) Size of tumor in cm³.
        7.  **``prefix``** (``c`` or ``p``) Prefix for tumor T-stage.
        8.  **``stage``** (``int``) T-stage of tumor.
    
    2. **``2``** Info about second tumor (if it exists) ...
       1. ...


3. **``{modality 1}``** Report of nodal involvement for ``{modality 1}``.
   1. **``info``** Quick info about the diagnosis.
      1. **``date``** (``date``) Date when diagnosis was taken.
   
   2. **``right``** Diagnosed involvement of the right side of the neck.
      1. **``I``** (``bool``) Involvement of LNL I
      2. **``II``** (``bool``) Involvement of LNL II
      3. **``III``** (``bool``) Involvement of LNL III
      4. ...
   
   3. **``left``** Diagnosed involvement of the left side of the neck.
      1. **``I``** (``bool``) Involvement of LNL I
      2. **``II``** (``bool``) Involvement of LNL II
      3. **``III``** (``bool``) Involvement of LNL III
      4. ...


4. **``{modality 2}``** Report of nodal involvement for ``{modality 2}``...
   1. ...

For most columns described here there exists a corresponding entry in the JSON file that comes with a key ``row`` for the row in which to find the value in the original Excel file, as well as a ``col`` for the column number and a key ``options`` or ``func``. With the ``options`` one can specify which values at the location ``[row,col]`` to map to which value in the final table. For example

```json
"options": {
    "yes": true,
    "no": false
}
```

simply reads any field containing "yes" as ``True`` and any field with "no" as ``False``. If anything else is found there, it interprets that as ``None``.

 Using ``func`` instead of ``option`` one specifies a string (e.g. ``"int"``, ``"age"``, ...) that the program understands as a function that will be used to interpret what it finds at row ``row`` and column ``col``. The complete list of functions it currently understands is

| function         | description                                                                                  |
| :--------------- | :------------------------------------------------------------------------------------------- |
| ``discard_char`` | convert e.g. "N2" to ``2`` by discarding the first character                                 |
| ``find_subsite`` | find subsite in array                                                                        |
| ``find_icd``     | find ICD code in array                                                                       |
| ``date``         | convert string in the format of YYYY-MM-DD into a date object                                |
| ``age``          | compute the patient's age from birthday and diagnose date (both locations must be specified) |
| ``str``          | interpret as lowercase string                                                                |
| ``int``          | interpret as integer                                                                         |
| ``float``        | interpret as decimal number                                                                  |
| ``bool``         | interpret as boolean                                                                         |
| ``nothing``      | do nothing                                                                                   |


## Usage

To collect all the extracted patients in a single CSV file, run the command ``python -m uszparser`` with the correct flags and arguments, which can be displayed by providing the ``--help`` flag:

```
usage: __main__.py [-h] [-j JSON] [-s SAVE] [-v] excel

positional arguments:
  excel                 Excel file that is supposed to be parsed

optional arguments:
  -h, --help            show this help message and exit
  -j JSON, --json JSON  JSON file that contains what to parse
  -s SAVE, --save SAVE  Where to save the resulting CSV file? (Default: "./parsed.csv")
  -v, --verbose         Give progress update
```

So, if you have a JSON file ``settings.json`` as well as the extraced Excel file ``extracted.xlsm`` in the current working directory, then you can run

```
python -m uszparser -j settings.json -s /path/to/your/output.csv extracted.xlsm
```

to parse the Excel file and save its output as CSV table.