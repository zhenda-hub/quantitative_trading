"""高频数据更新（每日）

行情快照与当日数据: efinance 股票/债券、集思录可转债、新闻、金属持仓、
行业板块、ETF 列表、yfinance 美股与加密货币。

用法: python -m utils.update_daily"""


import os
import re
from datetime import datetime
from pathlib import Path

import akshare as ak
import easyquotation as eq  # 国内
import efinance as ef  # 国内
import pandas as pd
import yfinance as yf  # 国际
from dotenv import load_dotenv
from func_timeout import FunctionTimedOut, func_timeout
from loguru import logger
from time import sleep

load_dotenv()
from utils.update_common import data_handler, ensure_dir, safe_call




def get_ak_jsl_bond():
    cookies = os.getenv("JISILU_COOKIES")
    df = safe_call(ak.bond_cb_jsl, cookie=cookies)
    if df is not None:
        if len(df) < 200:
            logger.error(
                f"jsl df get fail, need to login: https://www.jisilu.cn/data/cbnew/#cb"
            )
            return
        # breakpoint()
        filename = f"datas/raw/bonds/conv_{datetime.now().strftime('%Y%m%d')}.csv"
        df.to_csv(filename, index=False)
        logger.info(f"jsl债券数据: {filename} 已更新")


def get_ef_stock_data():
    """获取股票相关数据"""
    # 获取所有A股列表
    # date_str = datetime.now().strftime('%Y%m%d')

    for k in [
        "沪深A股",
        "美股",
        "港股",
        "行业板块",
        "概念板块",
        "可转债",
        "ETF",
    ]:
        # PE in data
        df = safe_call(ef.stock.get_realtime_quotes, k)
        if df is not None:
            filename = f"datas/raw/stocks/ef_{k}.csv"
            df.to_csv(filename, index=False)
            logger.info(f"ef {k} 数据: {filename} 已更新")


def get_ef_bond_data():
    """获取债券相关数据"""
    # date_str = datetime.now().strftime('%Y%m%d')
    # 获取可转债数据
    # bond_list = safe_call(ef.bond.get_realtime_quotes)
    # if bond_list is not None:
    #     filename = f"datas/raw/bonds/ef_bond_list_{date_str}.csv"
    #     bond_list.to_csv(filename, index=False)

    bond_base_info = safe_call(ef.bond.get_all_base_info)
    if bond_base_info is not None:
        filename = f"datas/raw/bonds/ef_get_all_base_info.csv"
        bond_base_info.to_csv(filename, index=False)
        logger.info(f"债券数据: {filename} 已更新")


def get_ef_futures_data():
    """获取期货相关数据"""
    # 获取期货合约列表
    date_str = datetime.now().strftime("%Y%m%d")
    futures_list = safe_call(ef.futures.get_realtime_quotes)
    if futures_list is not None:
        filename = f"datas/raw/futures/ef_futures_list_{date_str}.csv"
        ensure_dir(filename)
        futures_list.to_csv(filename, index=False)
        logger.info(f"期货合约列表数据: {filename} 已更新")


def get_ak_news_data():
    """获取 akshare 新闻数据"""
    date_str = datetime.now().strftime("%Y%m%d")

    # 全球财经直播
    df1 = safe_call(ak.stock_info_global_ths)
    if df1 is not None:
        filename = f"datas/raw/news/ak_stock_info_global_ths.csv"
        ensure_dir(filename)
        df1.to_csv(filename, index=False)
        logger.info(f"全球财经直播数据: {filename} 已更新")

    # 同花顺财经-电报
    df2 = safe_call(ak.stock_info_global_cls)
    if df2 is not None:
        filename = f"datas/raw/news/ak_stock_info_global_cls.csv"
        ensure_dir(filename)
        df2.to_csv(filename, index=False)
        logger.info(f"同花顺财经-电报数据: {filename} 已更新")

    # 东方财富-财经早餐
    df3 = safe_call(ak.stock_info_cjzc_em)
    if df3 is not None:
        filename = f"datas/raw/news/ak_stock_info_cjzc_em.csv"
        ensure_dir(filename)
        df3.to_csv(filename, index=False)
        logger.info(f"东方财富-财经早餐数据: {filename} 已更新")

    # stock_info_global_sina
    df4 = safe_call(ak.stock_info_global_sina)
    if df4 is not None:
        filename = f"datas/raw/news/ak_stock_info_global_sina.csv"
        ensure_dir(filename)
        df4.to_csv(filename, index=False)
        logger.info(f"新浪财经-全球财经新闻数据: {filename} 已更新")

    # stock_info_global_em
    df5 = safe_call(ak.stock_info_global_em)
    if df5 is not None:
        filename = f"datas/raw/news/ak_stock_info_global_em.csv"
        ensure_dir(filename)
        df5.to_csv(filename, index=False)
        logger.info(f"东方财富-全球财经新闻数据: {filename} 已更新")


def get_ak_metals_data():
    """获取 akshare 贵金属数据"""
    # date_str = datetime.now().strftime('%Y%m%d')
    # 黄金持仓数据
    gold_data = safe_call(ak.macro_cons_gold)

    if gold_data is not None:
        gold_data["单价"] = gold_data["总价值"] / gold_data["总库存"]
        gold_data["单价"] = gold_data["单价"].round(2)

        filename = f"datas/raw/metals/macro_cons_gold.csv"
        ensure_dir(filename)
        gold_data.to_csv(filename, index=False)
        logger.info(f"黄金持仓数据: {filename} 已更新")

    # 白银持仓数据
    silver_data = safe_call(ak.macro_cons_silver)

    if silver_data is not None:
        silver_data["单价"] = silver_data["总价值"] / silver_data["总库存"]
        silver_data["单价"] = silver_data["单价"].round(2)

        filename = f"datas/raw/metals/macro_cons_silver.csv"
        ensure_dir(filename)
        silver_data.to_csv(filename, index=False)
        logger.info(f"白银持仓数据: {filename} 已更新")


def get_ak_industry_data():
    """获取 akshare 行业数据"""
    date_str = datetime.now().strftime("%Y%m%d")

    # 行业分类数据

    industry_list = safe_call(ak.stock_sector_spot)
    if industry_list is not None:
        filename = f"datas/raw/n_indexes/ak_industry_list_{date_str}.csv"
        ensure_dir(filename)
        industry_list.to_csv(filename, index=False)
        logger.info(f"行业分类数据: {filename} 已更新")

    # industry_list_dfcf = ak.stock_board_industry_name_em()  # 行业板块-名称， 推荐
    # industry_list_ths = ak.stock_board_industry_summary_ths()  # 同花顺行业一览表
    # ak.stock_fund_flow_industry()
    # industry_list_xl = ak.stock_sector_spot()
    # logger.info("行业分类数据已更新")


def get_ak_bond_data():
    """获取 akshare 债券数据"""
    date_str = datetime.now().strftime("%Y%m%d")

    # 可转债数据
    conv_bond = safe_call(ak.bond_zh_cov)
    if conv_bond is not None:
        filename = f"datas/raw/bonds/ak_bond_zh_cov.csv"
        ensure_dir(filename)
        conv_bond.to_csv(filename, index=False)
        logger.info(f"可转债数据: {filename} 已更新")

    # 国债收益率数据
    bond_rate = safe_call(ak.bond_zh_us_rate)
    if bond_rate is not None:
        filename = f"datas/raw/bonds/ak_cn_us_rate.csv"
        ensure_dir(filename)
        bond_rate.to_csv(filename, index=False)
        logger.info(f"中美债券收益率数据: {filename} 已更新")


def get_ak_fund_data():
    """获取 akshare 基金数据"""
    date_str = datetime.now().strftime("%Y%m%d")

    # ETF基金列表
    etf_list = safe_call(ak.fund_etf_category_sina)
    if etf_list is not None:
        filename = f"datas/raw/funds/ak_etf_list_{date_str}.csv"
        ensure_dir(filename)
        etf_list.to_csv(filename, index=False)
        logger.info(f"ETF基金列表: {filename} 已更新")

    # # 基金公司数据
    # fund_aum = safe_call(ak.fund_aum_em)
    # if fund_aum is not None:
    #     filename = f"datas/raw/funds/ak_fund_aum_{date_str}.csv"
    #     ensure_dir(filename)
    #     fund_aum.to_csv(filename, index=False)
    #     logger.info(f"基金公司数据: {filename} 已更新")

    # ak.fund_portfolio_industry_allocation_em()  # 基金行业配置


def get_yf_market_data():
    """获取 yfinance 市场数据"""
    date_str = datetime.now().strftime("%Y%m%d")

    # 主要市场指数
    tickers = {
        "^GSPC": "SP500",
        "^DJI": "DowJones",
        "^IXIC": "NASDAQ",
        "^N225": "Nikkei225",
        "^FTSE": "FTSE100",
        "^GDAXI": "DAX",
        "000001.SS": "SSE",
        "399001.SZ": "SZSE",
    }

    # TODO: 获取SP500数据失败: Too Many Requests. Rate limited. Try after a while.

    # for symbol, name in tickers.items():
    #     try:
    #         ticker = yf.Ticker(symbol)
    #         # 获取历史数据
    #         hist = ticker.history(period="1y")
    #         filename = f"datas/raw/indexes/yf_{name}_{date_str}.csv"
    #         ensure_dir(filename)
    #         hist.to_csv(filename)
    #         logger.info(f"{name}指数数据已更新")
    #
    #         # 获取基本信息
    #         info = pd.Series(ticker.info)
    #         filename = f"datas/raw/indexes/yf_{name}_info_{date_str}.csv"
    #         ensure_dir(filename)
    #         info.to_csv(filename)
    #         logger.info(f"{name}指数信息已更新")
    #
    #     except Exception as e:
    #         logger.error(f"获取{name}数据失败: {str(e)}")


def get_yf_virtual_data():
    """获取 yfinance 虚拟货币历史数据

    支持的虚拟货币：
    - BTC-USD: Bitcoin (BTC)
    - ETH-USD: Ethereum (ETH)
    - XRP-USD: XRP (XRP)
    - BNB-USD: BNB (BNB)
    - SOL-USD: Solana (SOL)
    - USDT-USD: Tether (USDT)
    """
    # 虚拟货币映射: yfinance代码 -> 英文全名+缩写
    virtual_currencies = {
        "BTC-USD": "Bitcoin (BTC)",
        "ETH-USD": "Ethereum (ETH)",
        "XRP-USD": "XRP (XRP)",
        "BNB-USD": "BNB (BNB)",
        "SOL-USD": "Solana (SOL)",
        "USDT-USD": "Tether (USDT)",
    }

    for symbol, name in virtual_currencies.items():
        # 创建 Ticker 并获取历史数据的包装函数
        def fetch_virtual_data():
            ticker = yf.Ticker(symbol)
            return ticker.history(period="max")

        hist = safe_call(fetch_virtual_data)

        if hist is None:
            continue

        if hist.empty:
            logger.warning(f"{name}({symbol}) 数据为空，跳过")
            continue

        # 格式转换
        hist = hist.reset_index()
        hist["日期"] = hist["Date"].dt.strftime("%Y-%m-%d")
        hist = hist.rename(
            columns={
                "Close": "收盘",
                "Open": "开盘",
                "High": "高",
                "Low": "低",
                "Volume": "交易量",
            }
        )

        # 保存文件
        filename = f"datas/raw/virtual/{name}历史数据.csv"
        ensure_dir(filename)
        hist[["日期", "收盘", "开盘", "高", "低", "交易量"]].to_csv(
            filename, index=False
        )
        logger.info(f"{name}数据: {filename} 已更新，共 {len(hist)} 条记录")


def get_eq_stock_data():
    """
    eq stock, 没有有效数据
    """
    date_str = datetime.now().strftime("%Y%m%d")

    obj = eq.use("sina")
    res = obj.market_snapshot(prefix=True)
    df = pd.DataFrame(res).T.reset_index().rename(columns={"index": "code"})
    filename = f"datas/raw/stocks/eq_stocks_{date_str}.csv"
    df.to_csv(filename, index=False)
    logger.info(f"eq股票数据: {filename} 已更新")


def update_daily():
    """高频数据：行情快照 / 可转债 / 新闻 / 金属 / 行业 / 加密（目标 60s 内）

    注: get_ef_futures_data / get_eq_stock_data 属于实时快照, 默认不跑,
        需要时单独调用。
    """
    get_ef_stock_data()
    get_ef_bond_data()
    get_ak_jsl_bond()
    get_ak_bond_data()
    get_ak_news_data()
    get_ak_metals_data()
    get_ak_industry_data()
    get_ak_fund_data()
    get_yf_market_data()
    get_yf_virtual_data()


if __name__ == "__main__":
    from utils.set_log import set_log

    set_log("update_daily.log")
    update_daily()
