FROM python:slim

RUN ln -sf /usr/share/zoneinfo/Europe/Warsaw /etc/localtime

EXPOSE 8000

ARG USERNAME
ARG PASSWORD
# ARG LOG_LEVEL

ENV USERNAME=$USERNAME
ENV PASSWORD=$PASSWORD
# ENV LOG_LEVEL=$LOG_LEVEL

WORKDIR /app

###

COPY ../src/rund.sh /app
COPY ../src/requirements.txt /app
COPY ../src/main.py /app
COPY ../src/api.py /app
COPY ../src/cron.py /app
COPY ../src/moj_licznik.py /app

#RUN chmod +x /app/rund.sh
RUN pip install -r requirements.txt

RUN ls /app

CMD ["./rund.sh"]