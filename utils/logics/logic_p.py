from loguru import logger


def get_period(
    unemp_month_on_month: float,
    cpi_month_on_month: float,
    threshold: float = 0.05
) -> str:
    """根据失业率和CPI的环比变化判断经济周期阶段"""
    logger.info(f'unemp: {unemp_month_on_month}， cpi： {cpi_month_on_month}')

    if unemp_month_on_month > 0 and cpi_month_on_month > 0:
        if unemp_month_on_month > threshold and cpi_month_on_month > threshold:
            return '上升'
        else:
            return '高点'
    if unemp_month_on_month < 0 and cpi_month_on_month < 0:
        if abs(unemp_month_on_month) > threshold and abs(cpi_month_on_month) > threshold:
            return '下降'
        else:
            return '低点'

    return '未知'