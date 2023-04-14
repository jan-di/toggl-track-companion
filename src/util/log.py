import logging


class Log:
    @staticmethod
    def init() -> None:
        logging.basicConfig(level="DEBUG")

    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        return logging.getLogger(name)
