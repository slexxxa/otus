FROM python:3.9
RUN groupadd flask && useradd -g flask flask
RUN pip install Flask==3.0.3 && pip install psycopg2==2.9.10 && pip install prometheus_flask_exporter==0.23.1
WORKDIR /app
COPY app.py /app
USER flask
CMD ["python", "app.py"]
