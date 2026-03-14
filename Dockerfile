FROM mirror.gcr.io/python:3-slim

COPY requirements.txt requirements.txt
RUN pip install -U pip && pip install -r requirements.txt

WORKDIR /app
CMD ["flask", "run"]