from loguru import logger

def set_log():
    logger.add(
        'logs/debug.log',
        # mode='a',
        # format='{time} {level} {message}',
        level='DEBUG',
        rotation="1 week",  # Once the file is too old, it's rotated
        retention="6 months",  # Cleanup after some time
        # compression='zip'
    )