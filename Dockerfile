FROM python:3.11

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app

CMD ["python", "app/main.py"]
#CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]

# CMD ["python", "app/main.py"]

#EXPOSE 8080
#CMD ["uvicorn", "app.app:app", "--host", "0.0.0.0", "--port", "8080"]
