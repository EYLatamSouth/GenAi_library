"""
Definição: Classe de logging

Data: 11-10-2022
@author: EY - Data Consultant - Enzo.Medaglia

Etapas mandatórias:
    Tutorial:
    1. https://github.com/SpencerPao/Production_Pieces
    2. https://www.youtube.com/watch?v=mJm3YFzJBcA

Portable Logger anywhere for import.

"""
import logging
import logging.config
import yaml
import os

log = logging.getLogger(__name__)


class SetUpLogging():
    def __init__(self):
        self.default_config = os.path.join(os.path.dirname(
            os.path.abspath('__file__')), "logs/config/logging_config.yaml")

    def setup_logging(self, default_level=logging.INFO):
        path = self.default_config
        if os.path.exists(path):
            with open(path, 'rt') as f:
                config = yaml.safe_load(f.read())
                logging.config.dictConfig(config)
                logging.captureWarnings(True)
        else:
            logging.basicConfig(level=default_level)

# DECORATORS FOR LOGGING
# USE: @SetUpLogging.function_logger
    @staticmethod
    def function_logger(decorated_function):
        # DECORATOR FOR LOGGING FUNCTION
        # Criar "decorated_function",
        # Os parâmetros da função decorated_function podem variar então enviamos *args e **kwargs
        def new_function(*args, **kwargs):
            try:
                log.debug("Started function: " + decorated_function.__qualname__)
                return decorated_function(*args, **kwargs)
            except Exception:
                log.exception("Verify function " + decorated_function.__qualname__)
                raise
        # retornamos a função "new_function" e o valor da chamada à função original
        return new_function

    @staticmethod
    def class_logger(classe):
        # DECORATOR FOR LOGGING CLASS
        # Get all callable attributes of the class
        callable_attributes = {key: value for key, value in classe.__dict__.items()
                               if callable(value)}
        # Decorate each callable attribute of to the input class
        for name, decorated_function in callable_attributes.items():
            decorated = SetUpLogging.function_logger(decorated_function)
            setattr(classe, name, decorated)
        return classe
