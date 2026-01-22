import logging
import sys


class Colors:
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    GRAY = "\033[90m"


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors based on log level."""

    LEVEL_COLORS = {
        logging.DEBUG: Colors.GRAY,
        logging.INFO: Colors.GREEN,
        logging.WARNING: Colors.YELLOW,
        logging.ERROR: Colors.RED,
        logging.CRITICAL: Colors.MAGENTA,
    }

    def format(self, record):
        color = self.LEVEL_COLORS.get(record.levelno, Colors.WHITE)

        # Color the level name
        record.levelname = f"{color}{record.levelname}{Colors.RESET}"

        # Color the message based on content
        msg = record.msg
        if "===" in str(msg):
            record.msg = f"{Colors.CYAN}{msg}{Colors.RESET}"
        elif "---" in str(msg):
            record.msg = f"{Colors.BLUE}{msg}{Colors.RESET}"
        elif "Executing" in str(msg):
            record.msg = f"{Colors.YELLOW}{msg}{Colors.RESET}"
        elif "output:" in str(msg).lower():
            record.msg = f"{Colors.WHITE}{msg}{Colors.RESET}"

        return super().format(record)


def setup_colored_logging(level=logging.INFO):
    """Setup colored logging for the application."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(ColoredFormatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    ))

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers = []
    root_logger.addHandler(handler)
