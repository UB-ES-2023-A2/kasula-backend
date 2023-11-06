FROM python:3.11

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

ENV PORT 1234

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app

CMD exec uvicorn app.app_definition:app --host 0.0.0.0 --port ${PORT}
