import logging
class DualLogger:
    def __init__(self, name='apsimNGpy', log_file='apsimNGpy_sim.log', console_level=logging.DEBUG, file_level=logging.INFO):
        """
        Initialize the DualLogger.

        Parameters:
        -----------
        name : str
            The name of the logger.
        log_file : str
            The filename where logs will be saved.
        console_level : int
            The logging level for the console output.
        file_level : int
            The logging level for the file output.
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # Create console handler and set level
        console_handler = logging.StreamHandler()
        console_handler.setLevel(console_level)

        # Create file handler and set level
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(file_level)

        # Create formatter and set it for both handlers
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        # Add handlers to the logger
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

    def __call__(self, level, message):
        """
        Log a message at the given level.

        Parameters:
        -----------
        level : str
            The level at which to log the message ('debug', 'info', 'warning', 'error', 'critical').
        message : str
            The message to log.
        """
        if level == 'debug':
            self.logger.debug(message)
        elif level == 'info':
            self.logger.info(message)
        elif level == 'warning':
            self.logger.warning(message)
        elif level == 'error':
            self.logger.error(message)
        elif level == 'critical':
            self.logger.critical(message)
        else:
            raise ValueError(f"Invalid log level: {level}")

