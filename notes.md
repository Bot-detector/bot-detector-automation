# setup
creating a python venv to work in and install the project requirements
```
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```
# for admin purposes saving & upgrading
when you added some dependancies update the requirements
```
venv\Scripts\activate
call pip freeze > requirements.txt
```
when you want to upgrade the dependancies
```
venv\Scripts\activate
powershell "(Get-Content requirements.txt) | ForEach-Object { $_ -replace '==', '>=' } | Set-Content requirements.txt"
call pip install -r requirements.txt --upgrade
call pip freeze > requirements.txt
powershell "(Get-Content requirements.txt) | ForEach-Object { $_ -replace '>=', '==' } | Set-Content requirements.txt"
```