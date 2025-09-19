from loguru import logger
import pandas as pd
import akshare as ak  # 国内
import efinance as ef  # 国内
import easyquotation as eq  # 国内
# import yfinance as yf  # 国际

    
# df2 = ak.bond_cb_redeem_jsl()  # 强赎df
# ak.bond_zh_cov()  # 申购债券


# ak.index_investing_global_from_url('https://www.investing.com/indices/germany-30-futures', end_date='20550102')
# ak.index_investing_global(area="德国", symbol ="德国DAX30指数", period ="每日", start_date ="20050101", end_date ="20550605")
# df['Date'] = df['Date'].map(lambda x: x.strftime('%Y-%m-%d'))
ak.stock_board_industry_info_ths()



if __name__ == '__main__':

    
    ...
    
    breakpoint()   
    