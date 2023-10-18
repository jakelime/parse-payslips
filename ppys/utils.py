import logging

APP_NAME = "pdfdc"



def init_logger(name: str = "") -> logging.Logger:
    """
    initialize an logger (console output and file output)
    returns existing logger if already initialized before
    """
    logger_name = name if name else __name__
    logger = logging.getLogger(logger_name)
    if logger.hasHandlers():
        return logger
    c_handler = logging.StreamHandler()
    c_format = logging.Formatter("%(levelname)-8s: %(message)s")
    c_handler.setFormatter(c_format)
    c_handler.setLevel(logging.INFO)
    logger.addHandler(c_handler)
    logger_filename = (
        f"{logger_name}.log" if logger_name != "__main__" else f"{name}.log"
    )
    f_handler = logging.FileHandler(logger_filename)
    f_format = logging.Formatter(
        "[%(asctime)s]%(levelname)-8s: %(message)s", "%d-%b-%y %H:%M"
    )
    f_handler.setFormatter(f_format)
    f_handler.setLevel(logging.INFO)
    logger.addHandler(f_handler)
    logger.setLevel(logging.INFO)
    logger.info(f"logger initialized - {logger_filename}")
    return logger
