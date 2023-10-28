# Kasulà - Backend
  
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
```

## Run tests
```
pytest
```
Alternative
```
python app/run_tests.py
``` 