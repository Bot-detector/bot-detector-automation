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
python3 -m venv .venv
source .venv/bin/activate
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

kubectl port-forward -n kafka svc/bd-prd-kafka-service 9094:9094
kubectl port-forward -n database svc/mysql 3306:3306