FROM python:3.14
WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY users ./users
COPY users_app ./users_app
COPY manage.py ./

ARG DEBUG
ENV DEBUG=$DEBUG

RUN --mount=type=secret,id=django_secret_key \
    export DJANGO_SECRET_KEY=$(cat /run/secrets/django_secret_key) && \
    python manage.py migrate

EXPOSE 8000

CMD ["gunicorn", "users.wsgi", "--bind", "0.0.0.0:8000"]
