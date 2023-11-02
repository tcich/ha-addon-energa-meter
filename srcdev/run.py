import threading
import time, os, datetime
from api import app
from waitress import serve
import logging, configparser
from pathlib import Path
from moj_licznik import MojLicznik
from log_config import configure_logging

startup_task_completed = threading.Event()

def http_server():
    serve(app, host="0.0.0.0", port=8000, threads=8) 

# Jednorazowe zadanie przy starcie
def startup_task():
    mojLicznik = MojLicznik()
    logger.info("Rozpoczynam logowanie do Mój licznik.")
    logger.debug(f"Logowanie użytkownika {username}.")
    mojLicznik.login(username, password)
    if mojLicznik.loginStatus:
        logger.info(f"Aktualizacja liczników...")
        mojLicznik.update_countners()
        logger.info(f"Wyszukiwanie najstarszych danych...(Może to trwać kilkadziesiąt minut.)")
        mojLicznik.update_first_date()
        logger.info(f"Pobieranie danych...")
        mojLicznik.download_charts(full_mode=True)
        mojLicznik.update_last_days()
        #mojLicznik.set_daily_zones()
        logger.debug(f"Wylogowanie użytkownika.")
        mojLicznik.logout()
    startup_task_completed.set()

# Moduł 3: Cykliczne zadanie
def periodic_task():
    startup_task_completed.wait()
    while True:
        try:    
            waiting_seconds = 600
            logger.info(f"Oczekiwanie...")
            logger.debug(f"Czekam {waiting_seconds} sekund.")
            time.sleep(waiting_seconds)        
            mojLicznik = MojLicznik()
            logger.info(f"Update...{datetime.datetime.now()}")
            logger.info(f"Logowanie...")
            mojLicznik.login(username, password)
            if mojLicznik.loginStatus:
                logger.info(f"Aktualizacja danych bieżących...")
                mojLicznik.update_countners()
                mojLicznik.update_last_days()
                mojLicznik.download_charts(full_mode=False)
                # mojLicznik.set_daily_zones()
                mojLicznik.logout()
        except:
            logger.error("PT001: Błąd aktualizacji danych...")
    

# Uruchomienie wątków dla każdego modułu
if __name__ == "__main__":

    plik = Path('config.ini')
    username = None
    password = None
    log_level = None

    if plik.is_file():
        config = configparser.ConfigParser()
        config.read("config.ini")
        username = config.get("Credentials", "username")
        password = config.get("Credentials", "password")
        log_level = config.get("Logger", "log_level")
    else:
        username = os.getenv("USERNAME")
        password = os.getenv("PASSWORD")
        log_level = os.getenv("LOGLEVEL")

    logger_name = "energaMeter"

    configure_logging(log_level, logger_name)
    logger = logging.getLogger(logger_name)

    peewee_logger = logging.getLogger('peewee')
    peewee_logger.setLevel(logging.ERROR)  # Ustaw poziom na ERROR lub inny poziom, który jest wyższy niż ustawiony w configure_logging

    logger.info("Inicjalizacja OK.")
    http_server_thread = threading.Thread(target=http_server)
    startup_task_thread = threading.Thread(target=startup_task)
    periodic_task_thread = threading.Thread(target=periodic_task)

    http_server_thread.start()
    startup_task_thread.start()
    periodic_task_thread.start()

    http_server_thread.join()
    startup_task_thread.join()
    periodic_task_thread.join()
