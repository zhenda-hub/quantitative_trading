from loguru import logger
import pandas as pd
import akshare as ak  # 国内


def get_top_industries():
    pass


def get_top_3_by_industry(industry: str):
    pass


def get_datas_from_url(url: str):
    df = pd.read_html(url)
    breakpoint()
    
    
    
# df2 = ak.bond_cb_redeem_jsl()  # 强赎df
# ak.bond_zh_cov()  # 申购债券


# ak.index_investing_global_from_url('https://www.investing.com/indices/germany-30-futures', end_date='20550102')
# ak.index_investing_global(area="德国", symbol ="德国DAX30指数", period ="每日", start_date ="20050101", end_date ="20550605")
# df['Date'] = df['Date'].map(lambda x: x.strftime('%Y-%m-%d'))
ak.stock_board_industry_info_ths()


if __name__ == '__main__':
    ...
    