# Kasulà - Backend

Pre-release deployed on: https://kasula-v7-5q5vehm3ja-ew.a.run.app/

KASULÀ is a webpage where you can view and share recipes that mean the world to you.

## Prerequisites
- python >= 3

## Install
```
pip-compile requirements.in

python -m venv env
./env/Scripts/activate
pip install -r ./requirements.txt
```
Create a .env file in the config folder following the .env.example file. You will need to ask a developer the secret variables.

## Usage
```
./env/Scripts/activate
uvicorn app.app_definition:app # Alternative: python app/main.py
```

## Run tests
app/config/.env TEST_MODE=True (I'll delete it later)
```
pytest # Alternative: python app/run_tests.py
```

Windows
```
cmd /C "set TEST_MODE=True&& pytest"
```

Bash
```bash
TEST_MODE=True; pytest
```
 
