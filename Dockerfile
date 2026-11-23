FROM python:3.12-slim
WORKDIR /srv
COPY requirements.txt requirements-test.txt ./
RUN pip install --no-cache-dir -r requirements-test.txt
COPY . .
ENV MONITOR_DATABASE=/data/monitor.sqlite3
EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--threads", "4", "app.main:create_app()"]
