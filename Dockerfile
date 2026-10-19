# =====================================================================
#  THINGS YOU NEED TO EDIT / SET BEFORE DEPLOYING
# =====================================================================
#  1. Do NOT put passwords in this file. Set these environment variables
#     on the Aiven service (values come from your Aiven MySQL "Connection information"):
#        MYSQL_HOST      -> Aiven service host (e.g. xxx.aivencloud.com)
#        MYSQL_PORT      -> Aiven MySQL port (NOT always 3306)
#        MYSQL_USER      -> e.g. avnadmin
#        MYSQL_PASSWORD  -> your real password
#        MYSQL_DATABASE  -> must already exist on Aiven (default: customer_database)
#        MYSQL_SSL       -> true   (Aiven requires TLS)
#        MYSQL_SSL_CA    -> optional: path to Aiven's CA file to verify the certificate
#  2. config.py / config_local.example.py / render.yaml: replace the sample
#     password "1234" (and the "sync:" values in render.yaml) before going public.
#  3. Admin logins: after the first start, create them with  python add_user.py --admin
#     (run it once against the same database, e.g. from your own computer with the env vars set).
#  4. Port: the app listens on $PORT (default 8000). Change EXPOSE below only if the
#     platform needs a different port.
#  5. Data persistence: all data lives in MySQL, so nothing in this container needs a volume.
# =====================================================================

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Non-root user
RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

# Database settings come from environment variables (MYSQL_HOST, MYSQL_PORT, MYSQL_USER,
# MYSQL_PASSWORD, MYSQL_DATABASE, MYSQL_SSL) - set them in the Aiven / compose environment.
# Binds to 0.0.0.0 and honours $PORT if the platform provides one.
CMD ["sh", "-c", "python app.py --host 0.0.0.0 --port ${PORT:-8000} --trust-proxy"]
