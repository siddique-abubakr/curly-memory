import logging
import pathlib


class LogLevelFilter(logging.Filter):
    """
    LogLevelFilter is a filter that allows only messages
    with the specified level to pass.
    """

    def __init__(self, level):
        self.level = level

    def filter(self, record):
        return record.levelno == self.level


class Logger:
    """
    Logger is a singleton class that provides a logger.
    """

    _instance = None
    LOGS_DIR = "logs"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_LEVELS = [
        logging.DEBUG,
        logging.INFO,
        logging.WARNING,
        logging.ERROR,
        logging.CRITICAL,
    ]

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            pathlib.Path(cls.LOGS_DIR).mkdir(parents=True, exist_ok=True)
            cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance

    def __init__(self, name: str = __name__):
        if not hasattr(self, "logger"):
            self.logger = logging.getLogger(name)

            # Configuration
            self.logger.setLevel(logging.DEBUG)
            self.logger.addHandler(logging.StreamHandler())

            # File handlers
            formatter = logging.Formatter(self.LOG_FORMAT)
            for log_level in self.LOG_LEVELS:
                handler = logging.FileHandler(
                    pathlib.Path(self.LOGS_DIR)
                    / f"{logging.getLevelName(log_level).lower()}.log"
                )
                handler.setLevel(log_level)
                handler.setFormatter(formatter)
                handler.addFilter(LogLevelFilter(log_level))
                self.logger.addHandler(handler)

    @classmethod
    def get_logger(cls, name: str = __name__):
        return cls(name).logger
