
# slim (glibc): mediapipe nemá wheely pro Alpine (musl) ani pro Python > 3.12
FROM python:3.12-slim


WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libv4l-0 \
    && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt /app/requirements.txt


RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt


COPY ./app /app/app

# main.py importuje moduly a váhy relativně ke složce app/
WORKDIR /app/app
CMD ["python", "main.py"]
