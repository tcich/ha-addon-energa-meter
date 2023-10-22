import configparser, time, datetime, os
from moj_licznik import MojLicznik
from pathlib import Path

def main():
    plik = Path('config.ini')
    username = None
    password = None
    if plik.is_file():
        print(f"Pobieram parametry z config.ini.")
        config = configparser.ConfigParser()
        config.read("config.ini")
        username = config.get("Credentials", "username")
        password = config.get("Credentials", "password")
    else:
        username = os.getenv("USERNAME")
        password = os.getenv("PASSWORD")   
    try:
        mojLicznik = MojLicznik()
        print(f"Update...{datetime.datetime.now()}")
        print(f"Logowanie...")
        mojLicznik.login(username, password)
        if mojLicznik.loginStatus:
            print(f"Aktualizacja danych bieżących...")
            mojLicznik.uppdate_measurments()
            mojLicznik.update_last_days()
            mojLicznik.set_daily_zones()
            mojLicznik.logout()
    except:
        print("Błąd aktualizacji danych...")

if __name__ == "__main__":
    main()