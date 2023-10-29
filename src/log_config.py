import logging

def configure_logging(l_level, logger_name):
    log_level = getattr(logging, l_level.upper(), logging.INFO)
    logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    # Dodanie nazwy loggera do formatowania
    formatter = logging.Formatter('%(asctime)s - {} - %(levelname)s - %(message)s'.format(logger_name))
    console_handler.setFormatter(formatter)
    #logging.getLogger().addHandler(console_handler)

    print("Logowanie zostało skonfigurowane.")


