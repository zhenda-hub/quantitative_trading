import pdb

import yfinance as yf
from django.test import TestCase
from django.utils.timezone import now
import pandas_datareader as pdr
from quan_trad.local_settings import TUSHARE_TOKEN


# Create your tests here.
def test_get_data_yahoo():
    import tushare as ts
    pro = ts.pro_api(TUSHARE_TOKEN)
    #
    # # 获取全部可交易股票基础信息
    df = pro.hk_basic()
    pdb.set_trace()





