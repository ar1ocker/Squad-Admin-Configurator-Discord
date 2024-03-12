FROM python:3.10-alpine3.18

ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN adduser -u 5678 --disabled-password --gecos "" appuser

COPY ./requirements.txt ./

RUN pip3 install -r requirements.txt --no-cache-dir

COPY ./ ./

RUN chown -R appuser /app
USER appuser

CMD ["python", "squad_admin_configurator_discord/main.py"]
