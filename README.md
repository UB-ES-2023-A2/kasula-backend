# Kasulà - Backend
  
KASULÀ is a webpage where you can view and share recipes that mean the world to you.
  
## Installation
  
```powershell
pip-compile requirements.in
  
python -m venv env
./env/Scripts/activate
pip install -r .\requirements.txt
```
  
Create a .env file in config with the following content:
```
DEBUG_MODE=True
DB_URL=""
DB_NAME="kasuladb"
  
SECRET_KEY=""
```
Ask for the DB_URL and the SECRET_KEY
  
  
# Run
  
```powershell
python app/main.py
```