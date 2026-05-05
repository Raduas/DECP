# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
FROM tensorflow/tensorflow:latest-gpu
RUN apt-get update && apt-get install -y python3 python3-pip && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

#RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
RUN pip3 install --no-cache-dir tensorflow[and-cuda] && \
    pip3 install --no-cache-dir -r /code/requirements.txt
COPY ./app /code/app

CMD ["python", "app/main.py"]