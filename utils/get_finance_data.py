import yfinance as yf
import datetime
import pandas as pd


def get_maotai():
    # 定义起始日期和结束日期
    start_date = datetime.datetime.now() - datetime.timedelta(days=5 * 365)
    end_date = datetime.datetime.now()

    # 使用yfinance获取贵州茅台股票数据
    df = yf.download('600519.SS', start=start_date, end=end_date)


def get_all_stock_eq():
    """
    使用 easyquotation 获取所有数据
    """
    import easyquotation
    quotation = easyquotation.use('sina')  # 新浪 ['sina'] 腾讯 ['tencent', 'qq']
    d1 = quotation.market_snapshot(prefix=True)  # prefix 参数指定返回的行情字典中的股票代码 key 是否带 sz/sh 前缀
    df = pd.DataFrame(d1).T
    df.to_excel('useful_datas/all_data_by_eq.xlsx')
    d2 = quotation.real('162411')  # 支持直接指定前缀，如 'sh000001'


def get_cn_stock_ids():
    pass


def get_hk_stock_ids():
    pass


def get_usa_stock_ids():
    pass
