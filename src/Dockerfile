ARG BUILD_FROM
FROM $BUILD_FROM

RUN apk add --no-cache python3
RUN apk add --update py3-pip

# Copy data for add-on
COPY run.sh /
COPY run.py /
COPY requirements.txt /
COPY main.py /
COPY api.py /
COPY moj_licznik.py /
COPY log_config.py /
COPY database_empty.sqlite /database.sqlite
RUN chmod a+x /run.sh
RUN pip install -r requirements.txt

CMD [ "/run.sh" ]