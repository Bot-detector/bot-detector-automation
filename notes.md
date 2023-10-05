# setup
## windows
creating a python venv to work in and install the project requirements
```sh
python -m venv venv/windows/.venv
venv\windows\.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```
## linux
make sure to have pip
```sh
sudo apt install python3-pip
```
```sh
python3 -m venv venv/linux/.venv
source venv\linux\.venv\Scripts\activate
python3 -m pip install --upgrade pip
pip install -r requirements.txt
```
# for admin purposes saving & upgrading
when you added some dependancies update the requirements
```sh
venv\Scripts\activate
call pip freeze > requirements.txt
```
when you want to upgrade the dependancies
```sh
venv\Scripts\activate
powershell "(Get-Content requirements.txt) | ForEach-Object { $_ -replace '==', '>=' } | Set-Content requirements.txt"
call pip install -r requirements.txt --upgrade
call pip freeze > requirements.txt
powershell "(Get-Content requirements.txt) | ForEach-Object { $_ -replace '>=', '==' } | Set-Content requirements.txt"
```