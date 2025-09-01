from loguru import logger
import pandas as pd
import akshare as ak  # 国内


def get_top_industries():
    pass


def get_top_3_by_industry(industry: str):
    pass

    
# df2 = ak.bond_cb_redeem_jsl()  # 强赎df
# ak.bond_zh_cov()  # 申购债券


# ak.index_investing_global_from_url('https://www.investing.com/indices/germany-30-futures', end_date='20550102')
# ak.index_investing_global(area="德国", symbol ="德国DAX30指数", period ="每日", start_date ="20050101", end_date ="20550605")
# df['Date'] = df['Date'].map(lambda x: x.strftime('%Y-%m-%d'))
ak.stock_board_industry_info_ths()




# def get_maotai():
#     # 定义起始日期和结束日期
#     start_date = datetime.datetime.now() - datetime.timedelta(days=5 * 365)
#     end_date = datetime.datetime.now()
#
#     # 使用yfinance获取贵州茅台股票数据
#     df = yf.download('600519.SS', start=start_date, end=end_date)
#     pdb.set_trace()
#
#
# def get_all_stock_eq():
#     """
#     使用 easyquotation 获取所有数据
#     """
#     quotation = easyquotation.use('sina')  # 新浪 ['sina'] 腾讯 ['tencent', 'qq']
#     d1 = quotation.market_snapshot(prefix=True)  # prefix 参数指定返回的行情字典中的股票代码 key 是否带 sz/sh 前缀
#     df = pd.DataFrame(d1).T
#     d2 = quotation.real('162411')  # 支持直接指定前缀，如 'sh000001'
#     pdb.set_trace()


# def get_other_indexes():
#     # 下载日经225指数数据
#     nikkei = yf.Ticker("^N225")

#     # 获取历史数据时间范围
#     hist = nikkei.history(start="2010-01-01", end="2023-02-28")  # FIXME: not work

#     # 将数据转换为DataFrame
#     df = pd.DataFrame(hist)
#     breakpoint()





if __name__ == '__main__':
    import easyquotation as eq  # 国内
    obj = eq.use("sina")
    res = obj.market_snapshot(prefix=True)
    pd.DataFrame(res).T.to_csv('all_stocks.csv', index=False)
    breakpoint()
    
    
    
    
