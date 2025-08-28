import sys
from loguru import logger


def set_log(log_file: str):
    # logger.remove()
    # logger.add("script1.log", level="DEBUG")
    # logger.add(sys.stderr, level="INFO")  # 继续在控制台打印

    logger.add(
        f'logs/{log_file}',
        # format='{time} {level} {message}',
        level='DEBUG',
        rotation="1 day",      # 每天一个日志文件
        # rotation="1 week",  # Once the file is too old, it's rotated
        retention="7 days",    # 只保留 7 天
        # retention="6 months",  # Cleanup after some time
        compression="zip",     # 自动压缩归档
    )
