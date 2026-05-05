# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
FROM python:3.11.15

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app

CMD ["python", "app/main.py"]