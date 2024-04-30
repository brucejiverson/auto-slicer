
# Auto-Slicer

## Overview
Auto-Slicer is a CLI tool designed to automate the slicing of STL files based on a bill of materials (BOM) and manage 3D printing tasks via the OctoPi API.


## Dev notes
### Use case 1: STEP of assembly

1. get file
2. loop through all the steps

### Use case 2: folder with steps/stls (ie a download)
1. get folder
2. get bom
3. walk over that folder converting all step to stl in place
4. walk over folder for each stl

### Common to both
   1. auto slice, store gcode in a dict
   2. Keep metadata for each
      1. Quantity required
      2. Print time
      3. Volume
      4. Material volume + cost
      5. bed area
      6. height
   3. Upload in organized fashion
   4. Create a new continous print 


## Installation
To install the dependencies, run:
```bash
poetry install
```

prusa-slicer-console.exe must be in your path (Windows)

## Usage
To start the auto-slicing process, run:
```bash
poetry run auto-slicer
```

## Detail set up

For windows:
```
Invoke-WebRequest -UseBasicParsing -Uri "https://raw.githubusercontent.com/pyenv-win/pyenv-win/master/pyenv-win/install-pyenv-win.ps1" -OutFile "./install-pyenv-win.ps1"; &"./install-pyenv-win.ps1"
```

You may need to check your envrionment variables here. should be:
```
C:\Users\[YourUsername]\.pyenv\pyenv-win\bin

C:\Users\[YourUsername]\.pyenv\pyenv-win\shims
```

Continue:
```
pyenv install 3.12.1
pyenv global 3.12.1
python --version

pip install poetry
```


#### [OLD] Install git and python
```powershell
winget install -e --id Python.Python.3.12
winget install --id Git.Git -e --source winget
```

### 3) setup the development environment
```powershell
# navigate to the reference design source location
cd <path/to/auto-slicer>

# update pip
python.exe -m pip install --upgrade pip

# install poetry
python.exe -m pip install poetry

# optionally configure poetry to create virtual environments in the current package (allows vscode to detect)
poetry config virtualenvs.in-project true

# create venv
python.exe -m poetry env use python

# install dependencies
python.exe -m poetry install
```

### 4) test the environment works
Connect the reference design to the computer using USB and run:
```bash
python.exe -m poetry run cps test
```

Useful for altering/debugging
```
poetry env list  # shows the name of the current environment
poetry env remove <current environment>
poetry install  # will create a new environment using your updated configuration
```
