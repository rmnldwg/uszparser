# USZ Parser

Program for parsing the excel file that was created by Bertrand Pouymayou and then filled with patients by Jean-Marc Hoffmann. The excel file's particular structure makes it necessary to hard-code the location of all information. It is stored in the accompanying JSON file.

In its current state, the following info is extracted from the Excel file and grouped according to what I thought could fit:


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

For most columns described here there exists a corresponding entry in the JSON file that comes with a key ``row_loc`` for the row in which to find the value in the original Excel file, as well as a ``col_loc`` for the column number and a key ``func``. This last one specifies a string (e.g. ``"int"``, ``"age"``, ...) that the program understands as a function to interpret what it finds at ``row_loc``, ``col_loc``. The complete list of functions it currently understands is

| function         | description                                                                                  |
| :--------------- | :------------------------------------------------------------------------------------------- |
| ``yn2tf``        | convert "yes" & "no" to ``True`` & ``False`` (``None`` otherwise)                            |
| ``posneg2tf``    | convert "positive" & "negative" to ``True`` & ``False`` (``None`` otherwise)                 |
| ``discard_char`` | convert e.g. "N2" to ``2`` by discarding the first character                                 |
| ``find_subsite`` | find subsite in array                                                                        |
| ``find_icd``     | find ICD code in array                                                                       |
| ``date``         | convert string in the format of YYYY-MM-DD into a date object                                |
| ``age``          | compute the patient's age from birthday and diagnose date (both locations must be specified) |
| ``neck_dissect`` | convert "unilateral" & "no" to ``True`` & ``False`` (``None`` otherwise)                     |
| ``str``          | interpret as lowercase string                                                                |
| ``int``          | interpret as integer                                                                         |
| ``float``        | interpret as decimal number                                                                  |
| ``bool``         | interpret as boolean                                                                         |
| ``inv``          | return ``None`` if it is "unknown" and ``yn2tf`` otherwise                                   |
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