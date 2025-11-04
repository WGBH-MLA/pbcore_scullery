# pbcore-scullery
Utilities for analyzing PBCore XML data by fitting it in a tabular structure.

These routines require existing PBCore XML files.

The package is designed to be used by other Python modules by calling the `tablify` and `inframe` functions. It can also be used from the CLI.

## Installation

Clone the repository. Change to the repository directory and do a `pip install .` to install the package and its dependencies.

(For developers, do `pip install -e .` to install in editable mode.)

## Usage

### CLI

If you have a directory of PBCore XML files, you can create a CSV file from them by running:

```Shell
framify PATH/TO/YOUR/PBCORE/DIR PATH/TO/YOUR/OUTPUT.csv
```

To see additional options, run
```Shell
framify -h
```

### Importing into other Python projects

This package can be used in other Python projects by importing the `tablify` and `inframe` functions.

Sample code:
```Python
import pbcore_scullery as ps

pbcore_dir = "PATH/TO/YOUR/PBCORE/DIR"
assttbl, insttbl = ps.tablify(pbcore_dir)
asstdf, instdf, joindf = ps.inframe(assttbl, insttbl)

print("Asset dataframe:")
print(asstdf.head())
```

