
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


## Usage
To start the auto-slicing process, run:
```bash
poetry run auto-slicer
```
<!-- To propogate changes to dependent modules: appears incrementing version number and then poetry update is the only way -->


## Installation and set up
### Linux
#### Install initial tools and pyenv
```
sudo apt update && sudo apt upgrade
sudo apt install curl

# These are required for pyenv
sudo apt-get install -y build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev openssl git

curl https://pyenv.run | bash
```

#### Configure pyenv
The following is required for pyenv to work.

Add the following to the top of the .bashrc file:

```
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init --path)"
```
Add the following to the top of the .bashrc file:
```
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
```
Now, restart the terminal, and run `pyenv` as initial test that pyenv was install


#### Configure the environment and set up poetry
Ensure at this time that you have your pyproject.toml file in the root of your project and configured correctly with the poetry standards. If you're just trying to run the tests or examples, you can use the pyproject.toml file in this repo. Otherwise, you should have cloned this project, and you can define the path to this package in your pyproject.toml file.

Run the following commands to set up the environment and install poetry:
```
pyenv install 3.x.x
pyenv virtualenv 3.x.x <env_name>
pyenv local <env_name>
pip install poetry
poetry lock
poetry install
```

## Setting up backtests
See the examples folder for scripts demonstrating setting up and running backtests. `examples/simple_backtest.py` includes definitions of an algorithm, importing data from Alpaca, setting up common technical analysis indicators, running the backtest, and analyzing the performance of your algorithm.


### Windows
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

Navigate to your project. If new project, `poetry new <proj>`


#### [OLD] Install git and python 3.11.3
```powershell
winget install -e --id Python.Python.3.11
winget install --id Git.Git -e --source winget
```

### 2) setup SSH keys
Add your SSH keys to folder: `C:\Users\<username>\.ssh`

Then create the ssh config file `C:\Users\<username>\.ssh\config` and put:
```bash
Host gitlab.atomicmachines.com
    Preferredauthentications publickey
    IdentityFile ~/.ssh/id_rsa
    Port 22
```
Finally, verify SSH access to our gitlab server:
```bash
ssh git@gitlab.atomicmachines.com
```

You will see something like:
```bash
PS C:\Users\twoods> ssh git@gitlab.atomicmachines.com
PTY allocation request failed on channel 0
Welcome to GitLab, @<username>!
Connection to gitlab.atomicmachines.com closed.
```

### 3) setup the development environment
```powershell
# navigate to the reference design source location
cd <path/to/capacitive-parallelism-sensor>

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
