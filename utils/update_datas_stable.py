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
    
    
if __name__ == "__main__":
    from utils.set_log import set_log
    set_log('update_datas_stable.log')
    
    # 更新 akshare 数据
    get_ak_stock_data()
    