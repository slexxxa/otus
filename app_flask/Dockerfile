FROM python:3.9
RUN groupadd flask && useradd -g flask flask
RUN pip install Flask==3.0.3
WORKDIR /app
COPY app.py /app
USER flask
CMD ["python", "app.py"]
