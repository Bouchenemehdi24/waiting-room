import logging
import functools

def log_user_action(func):
    """
    Decorator to log user actions (function calls) to the terminal.
    Logs the function name and arguments each time the handler is called.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger("UserAction")
        logger.info(f"User action: {func.__name__} called with args={args[1:]}, kwargs={kwargs}")
        return func(*args, **kwargs)
    return wrapper