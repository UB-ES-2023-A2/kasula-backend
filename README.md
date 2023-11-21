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
python app/main.py
uvicorn app.app_definition:app  # Alternative: uvicorn directly
```

## Run tests
```
pytest # Using main database...
python app/run_tests.py  # Alternative: Using fancy script for tests
cmd /C "set DB_NAME=testsdb&& pytest" # Alternative: Windows, -s for prints
DB_NAME=testsdb; pytest # Alternative: Linux
```
