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

    print(f"Inicjacja...")
    mojLicznik = MojLicznik()
    print(f"Logowanie...", username)
    mojLicznik.login(username, password)
    if mojLicznik.loginStatus:
        print(f"Aktualizacja liczników...")
        mojLicznik.uppdate_measurments()
        print(f"Wyszukiwanie najstarszych danych...")
        mojLicznik.update_first_date()
        print(f"Pobieranie danych...")
        mojLicznik.download_charts(True)
        mojLicznik.update_last_days()
        mojLicznik.set_daily_zones()
        mojLicznik.logout()
 
if __name__ == "__main__":
    main()