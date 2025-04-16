import logging
import os
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from datetime import datetime

def setup_logging():
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Setup formatters for different purposes
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Setup file handlers with rotation
    # Main log file - rotate by size
    main_log = RotatingFileHandler(
        os.path.join(log_dir, 'app.log'),
        maxBytes=1024*1024,  # 1MB
        backupCount=5
    )
    main_log.setFormatter(detailed_formatter)
    main_log.setLevel(logging.INFO)
    
    # Error log file - rotate daily
    error_log = TimedRotatingFileHandler(
        os.path.join(log_dir, 'error.log'),
        when='midnight',
        interval=1,
        backupCount=30  # Keep 30 days of error logs
    )
    error_log.setFormatter(detailed_formatter)
    error_log.setLevel(logging.ERROR)
    
    # Console handler for development
    console = logging.StreamHandler()
    console.setFormatter(simple_formatter)
    console.setLevel(logging.DEBUG if os.getenv('DEV_MODE') else logging.INFO)
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture all levels
    root_logger.addHandler(main_log)
    root_logger.addHandler(error_log)
    root_logger.addHandler(console)
    
    # Log startup information
    root_logger.info("Logging system initialized")
    root_logger.info(f"Log directory: {log_dir}")
    
    return root_logger
