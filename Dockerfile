FROM python:3.12-slim

WORKDIR /app

# Install system dependencies (if any needed for pillow or playwright)
# Playwright needs browsers, but if we are just using the python client to control a remote or if we need to install browsers:
# For now, let's stick to basics. If playwright is used for search agent (web scraping), we need to install browsers.
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install google-auth-oauthlib google-auth google-api-python-client

# Install playwright browsers
RUN playwright install --with-deps chromium

COPY . .

# Expose port
EXPOSE 5000

# Environment variables should be passed at runtime, but we can set defaults
ENV FLASK_APP=app.py
ENV PORT=5000

CMD ["python", "app.py"]
