# Kasulà - Backend
  
KASULÀ is a webpage where you can view and share recipes that mean the world to you.
  
## Installation
```powershell
pip-compile requirements.in
  
python -m venv env
./env/Scripts/activate
pip install -r ./requirements.txt
```

## Configuration
Create a .env file in the config folder following the .env.example file. You will need to ask a developer the secret variables.
```
DEBUG_MODE=
DB_URL=""
DB_NAME=""

SECRET_KEY=""

GOOGLE_CLOUD_TOKEN=""
```
  
## Run
  
```powershell
./env/Scripts/activate
python app/main.py
```