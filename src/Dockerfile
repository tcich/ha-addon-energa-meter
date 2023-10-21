ARG BUILD_FROM
FROM $BUILD_FROM

RUN apk add --no-cache python3
RUN apk add --update py3-pip
# Copy data for add-on
COPY run.sh /
COPY requirements.txt /
COPY main.py /
COPY api.py /
COPY cron.py /
# COPY database.sqlite /
COPY moj_licznik.py /
RUN chmod a+x /run.sh
RUN pip install -r requirements.txt

CMD [ "/run.sh" ]