FROM python:3.9-slim-buster

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

#CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
