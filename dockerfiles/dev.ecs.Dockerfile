FROM python:3.10.10

COPY .. .

RUN pip install -r requirements.txt

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000", "--settings=chatnote.settings.dev"]

EXPOSE 8000
