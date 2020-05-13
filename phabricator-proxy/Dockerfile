FROM python:3

RUN pip install flask gunicorn requests

ADD main.py /

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "main:app"]