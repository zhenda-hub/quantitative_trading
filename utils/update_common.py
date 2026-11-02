"""数据更新公共件

safe_call    通用安全调用（带超时保护，超时/异常返回 None）
data_handler 更新函数装饰器（统一日志与异常兜底）
ensure_dir   确保目标文件所在目录存在

daily / weekly 两个更新入口共用本模块。"""


import os
import traceback
from functools import wraps
from datetime import datetime
from pathlib import Path

import pandas as pd
from func_timeout import FunctionTimedOut, func_timeout
from loguru import logger



def safe_call(func, *args, timeout_seconds=20, **kwargs):
    """通用安全调用函数，带超时保护（跨平台）

    超时时打印函数名到日志，返回 None，继续执行后续代码

    Args:
        func: 要调用的函数
        *args: 函数位置参数
        timeout_seconds: 超时时间（秒），默认 10
        **kwargs: 函数关键字参数

    Returns:
        函数返回值，超时或失败返回 None
    """
    try:
        return func_timeout(timeout_seconds, func, args=args, kwargs=kwargs)
    except FunctionTimedOut:
        logger.warning(
            f"【超时】{func.__name__} 调用超时 ({timeout_seconds}秒)，已跳过"
        )
        return None
    except Exception as e:
        logger.error(f"【失败】{func.__name__} 调用失败: {str(e)}")
        return None


SENSITIVE_KEYWORDS = ("cookie", "token", "secret", "password", "auth")


def _log_local_vars(frame):
    """记录出错帧的局部变量：截断长值、屏蔽敏感键、取值失败不影响主流程"""
    values = {}
    for key, value in list(frame.f_locals.items()):
        if any(word in key.lower() for word in SENSITIVE_KEYWORDS):
            values[key] = "***"
            continue
        try:
            values[key] = str(value)[:100]
        except Exception:  # noqa: BLE001 - __str__ 自身可能抛异常
            values[key] = f"<{type(value).__name__}>"
    if values:
        logger.error(f"  变量: {values}")


def data_handler(func):
    """数据获取函数装饰器：捕获异常并记录出错位置/类型/消息/局部变量，返回 None

    使用:
        @data_handler
        def get_ak_news_data():
            # 不需要 try-except
            df = safe_call(ak.stock_info_global_ths)
            ...
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as error:  # noqa: BLE001 - 统一兜底，不让单个数据源打断整轮更新
            trace = error.__traceback__
            # traceback 链的最后一帧 = 真正抛出异常的位置（不依赖文件名猜测）
            deepest = trace
            while deepest is not None and deepest.tb_next is not None:
                deepest = deepest.tb_next
            where = traceback.extract_tb(trace)[-1] if trace else None

            logger.error(f"【异常】{func.__name__} 执行失败")
            if where:
                logger.error(f"  位置: {where.filename}:{where.lineno} in {where.name}")
            logger.error(f"  类型: {type(error).__name__}")
            logger.error(f"  消息: {error}")
            if deepest is not None:
                _log_local_vars(deepest.tb_frame)

            return None

    return wrapper


# TODO: 目录改为日期


def ensure_dir(file_path):
    """确保目录存在"""
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)


