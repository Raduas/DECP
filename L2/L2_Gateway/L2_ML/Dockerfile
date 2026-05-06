# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
FROM pytorch/pytorch:2.11.0-cuda12.8-cudnn9-devel
#RUN apt-get update && apt-get install -y python3 python3-pip && \
#    rm -rf /var/lib/apt/lists/*
WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

#RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt


COPY ./app /code/app

CMD ["python", "app/main.py"]