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


# TODO: 目录改为日期

def ensure_dir(file_path):
    """确保目录存在"""
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)


def get_ak_stock_data():
    """获取 akshare 股票数据(code name)"""
    try:
        date_str = datetime.now().strftime('%Y%m%d')
        # A股个股列表
        stock_info = ak.stock_info_a_code_name()
        filename = f"datas/raw/stocks/ak_stock_list_{date_str}.csv"
        ensure_dir(filename)
        stock_info.to_csv(filename, index=False)
        logger.info("A股列表数据已更新")

    except Exception as e:
        logger.error(f"获取akshare股票数据失败: {str(e)}")


def get_ak_industry_data():
    """获取 akshare 行业数据"""
    try:
        date_str = datetime.now().strftime('%Y%m%d')
        
        # 行业分类数据
        
        industry_list = ak.stock_sector_spot()
        filename = f"datas/raw/n_indexes/ak_industry_list_{date_str}.csv"
        ensure_dir(filename)
        industry_list.to_csv(filename, index=False)
        logger.info("行业分类数据已更新")
        
        # industry_list_dfcf = ak.stock_board_industry_name_em()  # 行业板块-名称， 推荐
        # industry_list_ths = ak.stock_board_industry_summary_ths()  # 同花顺行业一览表
        # ak.stock_fund_flow_industry()
        # industry_list_xl = ak.stock_sector_spot()
        logger.info("行业分类数据已更新")

    except Exception as e:
        logger.error(f"获取akshare行业数据失败: {str(e)}")
        

def get_ak_bond_data():
    """获取 akshare 债券数据"""
    try:
        date_str = datetime.now().strftime('%Y%m%d')
        
        # 可转债数据
        conv_bond = ak.bond_zh_cov()
        filename = f"datas/raw/bonds/ak_bond_zh_cov_{date_str}.csv"
        ensure_dir(filename)
        conv_bond.to_csv(filename, index=False)
        logger.info("可转债数据已更新")

        # 国债收益率数据
        try:
            bond_rate = ak.bond_zh_us_rate()
            filename = f"datas/raw/bonds/ak_cn_us_rate_{date_str}.csv"
            ensure_dir(filename)
            bond_rate.to_csv(filename, index=False)
            logger.info("中美债券收益率数据已更新")
        except Exception as e:
            logger.error(f"获取中美债券收益率失败: {str(e)}")

    except Exception as e:
        logger.error(f"获取akshare债券数据失败: {str(e)}")
        
        
def get_ak_fund_data():
    """获取 akshare 基金数据"""
    try:
        date_str = datetime.now().strftime('%Y%m%d')
        
        # ETF基金列表
        etf_list = ak.fund_etf_category_sina()
        filename = f"datas/raw/funds/ak_etf_list_{date_str}.csv"
        ensure_dir(filename)
        etf_list.to_csv(filename, index=False)
        logger.info("ETF基金列表已更新")

        # 基金规模数据
        fund_aum = ak.fund_aum_em()
        filename = f"datas/raw/funds/ak_fund_aum_{date_str}.csv"
        ensure_dir(filename)
        fund_aum.to_csv(filename, index=False)
        logger.info("基金规模数据已更新")

        # ak.fund_portfolio_industry_allocation_em()  # 基金行业配置
    except Exception as e:
        logger.error(f"获取akshare基金数据失败: {str(e)}")
    
    
def get_ak_macro_data():
    """获取 akshare 宏观经济数据"""
    try:
        # CPI数据
        get_ak_cpi_data()

        # GDP数据
        get_ak_gdp_data()
        
        # date_str = datetime.now().strftime('%Y%m%d')

        # # 中国PMI数据
        # pmi_data = ak.macro_china_pmi_yearly()
        # filename = f"datas/raw/macro/ak_china_pmi_{date_str}.csv"
        # ensure_dir(filename)
        # pmi_data.to_csv(filename, index=False)
        # logger.info("中国PMI数据已更新")
        
        # # 中国货币供应量
        # money_supply = ak.macro_china_money_supply()
        # filename = f"datas/raw/macro/ak_china_money_supply_{date_str}.csv"
        # ensure_dir(filename)
        # money_supply.to_csv(filename, index=False)
        # logger.info("中国货币供应量数据已更新")

    except Exception as e:
        logger.error(f"获取akshare宏观数据失败: {str(e)}")


def get_ak_cpi_data():
    
    # date_str = datetime.now().strftime('%Y%m%d')
    
    # cpi消费者物价指数
    cpi_cn_data = ak.macro_china_cpi_yearly()
    filename = f"datas/raw/cpis/macro_china_cpi_yearly.csv"
    ensure_dir(filename)
    cpi_cn_data.to_csv(filename, index=False)
    logger.info("中国CPI数据已更新")
    
    # cpi 美国
    cpi_usa = ak.macro_usa_cpi_yoy()
    filename = f"datas/raw/cpis/macro_usa_cpi_yoy.csv"
    ensure_dir(filename)
    cpi_usa.to_csv(filename, index=False)
    logger.info("美国CPI数据已更新")
    # cpi 欧元区
    cpi_enro = ak.macro_euro_cpi_yoy()
    filename = f"datas/raw/cpis/macro_euro_cpi_yoy.csv"
    ensure_dir(filename)
    cpi_enro.to_csv(filename, index=False)
    logger.info("欧元区CPI数据已更新")
    
    # cpi 澳大利亚
    cpi_australia = ak.macro_australia_cpi_yearly()
    filename = f"datas/raw/cpis/macro_australia_cpi_yearly.csv"
    ensure_dir(filename)
    cpi_australia.to_csv(filename, index=False)
    logger.info("澳大利亚CPI数据已更新")
    
    # cpi 加拿大
    cpi_canada = ak.macro_canada_cpi_yearly()
    filename = f"datas/raw/cpis/macro_canada_cpi_yearly.csv"
    ensure_dir(filename)
    cpi_canada.to_csv(filename, index=False)
    logger.info("加拿大CPI数据已更新")
    
    # cpi 日本
    cpi_japan = ak.macro_japan_cpi_yearly()
    filename = f"datas/raw/cpis/macro_japan_cpi_yearly.csv"
    ensure_dir(filename)
    cpi_japan.to_csv(filename, index=False)
    logger.info("日本CPI数据已更新")
    
    
def get_ak_gdp_data():
    
    # date_str = datetime.now().strftime('%Y%m%d')
    # china gdp
    china_gdp = ak.macro_china_gdp_yearly()
    filename = f"datas/raw/gdps/ak_china_gdp.csv"
    ensure_dir(filename)
    china_gdp.to_csv(filename, index=False)
    logger.info("中国GDP数据已更新")
    
    # usa gdp
    usa_gdp = ak.macro_usa_gdp_monthly()  # usa gdp
    filename = f"datas/raw/gdps/ak_usa_gdp.csv"
    ensure_dir(filename)
    usa_gdp.to_csv(filename, index=False)
    logger.info("美国GDP数据已更新")
    
    # euro gdp
    enro_gdp = ak.macro_euro_gdp_yoy()  # euro gdp
    filename = f"datas/raw/gdps/ak_euro_gdp.csv"
    ensure_dir(filename)
    enro_gdp.to_csv(filename, index=False)
    logger.info("欧元区GDP数据已更新")
    

def get_yf_market_data():
    """获取 yfinance 市场数据"""
    try:
        date_str = datetime.now().strftime('%Y%m%d')
        
        # 主要市场指数
        tickers = {
            '^GSPC': 'SP500',
            '^DJI': 'DowJones',
            '^IXIC': 'NASDAQ',
            '^N225': 'Nikkei225',
            '^FTSE': 'FTSE100',
            '^GDAXI': 'DAX',
            '000001.SS': 'SSE',
            '399001.SZ': 'SZSE'
        }
        
        # todo:check
        
        # for symbol, name in tickers.items():
        #     try:
        #         ticker = yf.Ticker(symbol)
        #         # 获取历史数据
        #         hist = ticker.history(period="1y")
        #         filename = f"datas/raw/indexes/yf_{name}_{date_str}.csv"
        #         ensure_dir(filename)
        #         hist.to_csv(filename)
        #         logger.info(f"{name}指数数据已更新")
                
        #         # 获取基本信息
        #         info = pd.Series(ticker.info)
        #         filename = f"datas/raw/indexes/yf_{name}_info_{date_str}.csv"
        #         ensure_dir(filename)
        #         info.to_csv(filename)
        #         logger.info(f"{name}指数信息已更新")
                
        #     except Exception as e:
        #         logger.error(f"获取{name}数据失败: {str(e)}")

    except Exception as e:
        logger.error(f"获取yfinance数据失败: {str(e)}")


def get_ef_stock_data():
    """获取股票相关数据"""
    try:
        # 获取所有A股列表
        date_str = datetime.now().strftime('%Y%m%d')
        stock_list = ef.stock.get_realtime_quotes()
        filename = f"datas/raw/stocks/ef_stock_list_{date_str}.csv"
        stock_list.to_csv(filename, index=False)
        logger.info("股票列表数据已更新")

        # 获取上证50、沪深300、中证500成分股
        index_codes = {
            'sh000016': '上证50',
            'sh000300': '沪深300',
            'sh000905': '中证500'
        }
        
        # df_dict = ef.stock.get_quote_history(code)
        
        # for code, name in index_codes.items():
        #     try:
            #     for period, df in df_dict.items():
            #         fname = f"ef_{name}_{period}_{date_str}.csv"
            #         filename = f"datas/raw/stocks/{fname}"
            #         df.to_csv(filename, index=False)
            #     logger.info(f"{name}历史数据已更新")
            # except Exception as e:
            #     logger.error(f"获取{name}历史数据失败: {str(e)}")

    except Exception as e:
        logger.error(f"获取股票数据失败: {str(e)}")


def get_ef_fund_data():
    """获取基金相关数据"""
    try:
        date_str = datetime.now().strftime('%Y%m%d')
        # 获取所有基金列表
        fund_list = ef.fund.get_quote_history('159949')  # 获取华安创业板50ETF作为示例
        filename = f"datas/raw/funds/ef_fund_list_{date_str}.csv"
        fund_list.to_csv(filename, index=False)
        logger.info("基金数据已更新")

    except Exception as e:
        logger.error(f"获取基金数据失败: {str(e)}")


def get_ef_bond_data():
    """获取债券相关数据"""
    try:
        date_str = datetime.now().strftime('%Y%m%d')
        # 获取可转债数据
        bond_list = ef.bond.get_realtime_quotes()
        filename = f"datas/raw/bonds/ef_bond_list_{date_str}.csv"
        bond_list.to_csv(filename, index=False)
        
        bond_base_info = ef.bond.get_all_base_info()
        filename = f"datas/raw/bonds/ef_bond_base_info_{date_str}.csv"
        bond_base_info.to_csv(filename, index=False)
        logger.info("债券数据已更新")

    except Exception as e:
        logger.error(f"获取债券数据失败: {str(e)}")


def get_ef_futures_data():
    """获取期货相关数据"""
    try:
        # 获取期货合约列表
        date_str = datetime.now().strftime('%Y%m%d')
        futures_list = ef.futures.get_realtime_quotes()
        filename = f"datas/raw/futures/ef_futures_list_{date_str}.csv"
        ensure_dir(filename)
        futures_list.to_csv(filename, index=False)
        logger.info("期货合约列表数据已更新")

    except Exception as e:
        logger.error(f"获取期货数据失败: {str(e)}")


def get_ak_jsl_bond():
    try:
        cookies = os.getenv('JISILU_COOKIES')
        df = ak.bond_cb_jsl(cookie=cookies)
        breakpoint()
        df.to_csv(f'datas/raw/bonds/conv_{datetime.now().strftime("%Y%m%d")}.csv', index=False)    
        logger.info("jsl债券数据已更新")

    except Exception as e:
        logger.error(f"获取jsl债券数据失败: {str(e)}")
    


def ana_bonds(bond_id2names: dict):
    """
    对特定债券进行分析
    """
    for bond_id, bond_name in bond_id2names.items():
        df_detail = ak.bond_zh_cov_value_analysis(bond_id)
        breakpoint()
        df_detail.to_csv(f'datas/raw/bonds/details/{bond_name}.csv', index=False)


def get_eq_stock_data():
    date_str = datetime.now().strftime('%Y%m%d')
    
    obj = eq.use("sina")
    res = obj.market_snapshot(prefix=True)
    df = pd.DataFrame(res).T.reset_index().rename(columns={"index": "code"})
    df.to_csv(f'datas/raw/stocks/eq_stocks_{date_str}.csv', index=False)
    logger.info("eq股票数据已更新")


if __name__ == "__main__":
    from utils.set_log import set_log
    set_log('update_datas.log')
    
    # 更新 akshare 数据
    # get_ak_stock_data()
    get_ak_bond_data()
    get_ak_jsl_bond()
    get_ak_fund_data()
    get_ak_macro_data()
    
    # 更新 efinance 数据
    get_ef_stock_data()
    # get_ef_fund_data()
    get_ef_bond_data()
    # get_ef_futures_data()
    
    # 更新 yfinance 数据
    get_yf_market_data()
