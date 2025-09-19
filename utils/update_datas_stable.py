import os
from datetime import datetime

from loguru import logger
from dotenv import load_dotenv
import akshare as ak
import efinance as ef  # 国内
import yfinance as yf  # 国际
import easyquotation as eq  # 国内
import pandas as pd

load_dotenv()


def ensure_dir(file_path):
    """确保目录存在"""
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)


def get_ak_stock_data():
    """获取 akshare 股票数据(code name), 没什么变化, 不用每天更新"""
    try:
        date_str = datetime.now().strftime('%Y%m%d')
        # A股个股列表
        stock_info = ak.stock_info_a_code_name()
        filename = f"datas/raw/stocks/ak_stock_list_{date_str}.csv"
        ensure_dir(filename)
        stock_info.to_csv(filename, index=False)
        logger.info(f"A股列表数据: {filename} 已更新")

    except Exception as e:
        logger.error(f"获取akshare股票数据失败: {str(e)}")


def get_ak_index_global_data():
    """获取 akshare 全球指数数据"""
    try:
        date_str = datetime.now().strftime('%Y%m%d')
        # 全球指数列表
        index_global = ak.index_global_spot_em()
        filename = f"datas/raw/indexes/ak_index_global_spot_em_{date_str}.csv"
        ensure_dir(filename)
        index_global.to_csv(filename, index=False)
        logger.info(f"全球指数列表数据: {filename} 已更新")
        
        for symbol in index_global['指数代码'].unique():
            df = ak.index_global_hist_em(symbol=symbol)
            filename = f"datas/raw/indexes/ak_index_global_hist_em_{symbol}_{date_str}.csv"
            ensure_dir(filename)
            df.to_csv(filename, index=False)
            logger.info(f"全球指数 {symbol} 数据: {filename} 已更新")

    except Exception as e:
        logger.error(f"获取akshare全球指数数据失败: {str(e)}")
    
    
if __name__ == "__main__":
    from utils.set_log import set_log
    set_log('update_datas_stable.log')
    
    # 更新 akshare 数据
    get_ak_stock_data()
    get_ak_index_global_data()
    