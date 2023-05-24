import datetime
import time
import pdb

import yfinance as yf
import pandas as pd
import akshare as ak
import easyquotation


def get_maotai():
    # 定义起始日期和结束日期
    start_date = datetime.datetime.now() - datetime.timedelta(days=5 * 365)
    end_date = datetime.datetime.now()

    # 使用yfinance获取贵州茅台股票数据
    df = yf.download('600519.SS', start=start_date, end=end_date)
    pdb.set_trace()


def get_all_stock_eq():
    """
    使用 easyquotation 获取所有数据
    """
    quotation = easyquotation.use('sina')  # 新浪 ['sina'] 腾讯 ['tencent', 'qq']
    d1 = quotation.market_snapshot(prefix=True)  # prefix 参数指定返回的行情字典中的股票代码 key 是否带 sz/sh 前缀
    df = pd.DataFrame(d1).T
    d2 = quotation.real('162411')  # 支持直接指定前缀，如 'sh000001'
    pdb.set_trace()


def get_every_type_ak():
    # FIXME
    # df = ak.stock_zcfz_em('20230425')  # 资产负债表
    # df2 = ak.stock_lrb_em('20230425')  # 利润表
    # df3 = ak.stock_xjll_em('20230425')  # 现金流量表
    funcs = [
        ak.stock_info_a_code_name,  # 所有股票代码
        ak.reits_realtime_em,  # reits
        ak.index_value_name_funddb,  # 指数
        # 港股
        ak.stock_zh_ah_daily,  # 港股历史行情
        ak.stock_zh_ah_spot,  # 港股实时行情
        # A股
        ak.stock_zh_a_spot,  # 实时数据
        ak.stock_zh_a_daily,  # 个股历史数据
        ak.stock_zh_a_cdr_daily,  # 个股历史cdr数据
        ak.stock_zh_a_minute,  # 个股历史min数据
    ]
    for func in funcs:
        df = func()
        pdb.set_trace()
        time.sleep(2)


def get_cn_stock_ids():
    pass


def get_hk_stock_ids():
    pass


def get_usa_stock_ids():
    pass
