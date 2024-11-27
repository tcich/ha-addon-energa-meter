ARG BUILD_FROM
FROM $BUILD_FROM

RUN apk add --no-cache python3

WORKDIR /app
COPY requirements.txt .

# Copy data for add-on
COPY run.sh .
COPY run.py .
COPY main.py .
COPY api.py .
COPY moj_licznik.py .
COPY log_config.py .
COPY database_empty.sqlite data/database.sqlite
RUN chmod a+x run.sh

RUN apk add --update --no-cache py3-pip && \
    python3 -m venv /app/venv && \
    source /app/venv/bin/activate && \
    pip install -r requirements.txt

CMD [ "/app/run.sh" ]
