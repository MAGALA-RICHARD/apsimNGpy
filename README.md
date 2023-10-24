# apsimNGpy

An advanced open-source Python library that for agroecosystem modeling encompassing optimization, fast batch file simulation,  model prediction, evaluation, apsimx file editing, weather data retrieval, and soil profile development.

## Installation

Dotnet installation is required to run the code https://dotnet.microsoft.com/en-us/download/dotnet/7.0. 
## method 1
```
pip install git+https://github.com/MAGALA-RICHARD/apsimNGpy.git
```
## method 2
```
```
git clone https://github.com/MAGALA-RICHARD/apsimNGpy.git
cd apsimNGpy
pip install .

```

## APSIM interface

Install APSIM and ensure that the directory containing the Models executable is added to the system's PATH or the Python path (to locate the required .dll files). This can be achieved in either of the following ways:

a. Utilize the APSIM installer provided for this purpose.

b. Build APSIM from its source code. This is soon

## Source build

```bash
we are working on fixing this

```

## Usage:
.. code:: python
import apsimNGpy
from apsimNGpy.base_data import load_example_files
from apsimNGpy.apsimpy import ApsimSoil
from pathlib import Path
cwd = Path.cwd()
# create the data
data = load_example_files(cwd)
# get maize model
maize = data.get_maize
print(maize)
## initialise the apsimsoil instac eobject
apsim = ApsimSoil(maize, copy = True)
# run the file
apsim.run_edited_file()
print(apsim.results)

```



