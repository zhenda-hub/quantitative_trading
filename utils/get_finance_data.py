import yfinance as yf
import datetime


def get_maotai():
    # 定义起始日期和结束日期
    start_date = datetime.datetime.now() - datetime.timedelta(days=5 * 365)
    end_date = datetime.datetime.now()

    # 使用yfinance获取贵州茅台股票数据
    df = yf.download('600519.SS', start=start_date, end=end_date)


def get_cn_stock_ids():
    pass


def get_hk_stock_ids():
    pass


def get_usa_stock_ids():
    pass
