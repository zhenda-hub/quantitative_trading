"""低频数据更新（每周 / 每月）

REITs 与全球指数的历史序列及其合并、宏观 CPI/GDP、标准口径 GDP/CPI、
A股代码名称列表等变化缓慢的数据。

用法: python -m utils.update_weekly"""


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
from utils.cpi_std import build_std_cpi
from utils.gdp_std import build_std_gdp




def get_ak_reits_data():
    """
    获取 akshare reits 数据
    """
    # date_str = datetime.now().strftime('%Y%m%d')
    # reits列表
    reits_list = safe_call(ak.reits_realtime_em)
    if reits_list is not None:
        filename = f"datas/raw/reits/reits_realtime_em.csv"
        ensure_dir(filename)
        reits_list.to_csv(filename, index=False)
        logger.info(f"REITs列表数据: {filename} 已更新")

        # reits_hist_em

        for symbol, name in zip(reits_list["代码"], reits_list["名称"]):
            df = safe_call(ak.reits_hist_em, symbol=symbol)
            if df is not None:
                filename = f"datas/raw/reits/reits_hist_em_{symbol}_{name}.csv"
                ensure_dir(filename)
                df.to_csv(filename, index=False)
                logger.info(f"REITs {symbol} 数据: {filename} 已更新")

    # merge_ak_reits()


def merge_ak_reits():
    """
    读取多个 akshare REITs 数据, pd.merge 合并后保存为一个csv文件, 方便绘图
    """
    reits_dir = Path("datas/raw/reits")
    output_dir = Path("datas/processed/reits")
    output_dir.mkdir(parents=True, exist_ok=True)

    for csv_file in sorted(reits_dir.glob("reits_hist_em_*.csv")):
        try:
            df_tmp = pd.read_csv(csv_file)
            if "日期" in df_tmp.columns and "今开" in df_tmp.columns:
                # 解析日期
                dates = pd.to_datetime(df_tmp["日期"], errors="coerce")
                vals = pd.to_numeric(df_tmp["今开"], errors="coerce")

                name = csv_file.stem.replace("reits_hist_em_", "")

                # 合并数据
                if "merged_df" in locals():
                    merged_df = pd.merge(
                        merged_df,
                        pd.DataFrame({"日期": dates, name: vals}),
                        on="日期",
                        how="outer",
                    )
                else:
                    merged_df = pd.DataFrame({"日期": dates, name: vals})

        except Exception as e:
            logger.warning(f"读取文件 {csv_file} 失败: {e}")

    # 保存合并后的数据
    if "merged_df" in locals():
        merged_df.sort_values("日期", inplace=True)
        merge_file = output_dir / "reits_merged.csv"
        merged_df.to_csv(merge_file, index=False)
        logger.info(f"REITs合并数据已保存: {merge_file}")

    else:
        logger.warning("没有可合并的REITs数据")


# 全球指数名单(唯一来源): spot 接口失败时用它兜底; merge_ak_index() 也用它筛选 csv
FALLBACK_INDEX_SYMBOLS = [
    "道琼斯",
    "标普500",
    "纳斯达克",
    "加拿大S&PTSX",
    "巴西BOVESPA",
    "富时100",
    "德国DAX",
    "法国CAC",
    "日经225",
    "韩国KOSPI",
    "上证指数",
    "深证成指",
    "恒生指数",
    "沪深300",
    "澳大利亚标普200",
    "印度孟买SENSEX",
    "越南",
]


def get_ak_index_global_data():
    """
    获取 akshare 全球指数数据

    spot 接口只用来拿指数名单, 不能让它成为单点依赖:
    spot 失败时回落到 FALLBACK_INDEX_SYMBOLS, 历史数据照常刷新。
    """
    # 1) 拿指数名单 (带重试)
    index_global = None
    for attempt in range(1, 4):
        index_global = safe_call(ak.index_global_spot_em, timeout_seconds=30)
        if index_global is not None:
            break
        logger.warning(f"全球指数列表获取失败(第 {attempt}/3 次)")
        if attempt < 3:
            sleep(5)

    symbols = None
    if index_global is not None:
        filename = f"datas/raw/indexes/ak_index_global_spot_em.csv"
        ensure_dir(filename)
        index_global.to_csv(filename, index=False)
        logger.info(f"全球指数列表数据: {filename} 已更新")
        symbols = list(index_global["名称"].unique())

    if not symbols:
        symbols = FALLBACK_INDEX_SYMBOLS
        logger.warning(
            f"全球指数名单不可用, 回落到内置名单, 共 {len(symbols)} 个指数"
        )

    # 2) 逐个刷新历史数据
    ok, fail = 0, 0
    for symbol in symbols:
        df = safe_call(ak.index_global_hist_em, symbol=symbol, timeout_seconds=30)
        if df is None or df.empty:
            fail += 1
            continue
        filename = f"datas/raw/indexes/ak_index_global_hist_em_{symbol.replace('/', '')}.csv"
        ensure_dir(filename)
        df.to_csv(filename, index=False)
        logger.info(f"全球指数 {symbol} 数据: {filename} 已更新")
        ok += 1

    logger.info(f"全球指数历史数据更新完成: 成功 {ok} 个, 失败 {fail} 个")

    # merge_ak_index()


def merge_ak_index():
    """
    读取多个 akshare 全球指数数据, pd.merge 合并后保存为一个csv文件, 方便绘图
    数据的columns: 日期, 名称1, 名称2, 名称3, ...

    数据为归一化值
    min-max 会扭曲涨跌幅，只能表示区间位置，所以不能用。只有 x/start 才能表达真实涨跌率，是金融标准做法

    基准归一化（x / start）

    归一化后保留两位小数
    归一化后保存为新的csv文件
    方便后续绘图使用

    """

    index_dir = Path("datas/raw/indexes")
    output_dir = Path("datas/processed/indexes")
    output_dir.mkdir(parents=True, exist_ok=True)

    csvs = []
    for csv_file in index_dir.glob("ak_index_global_hist_em_*.csv"):
        if any(
            tc in csv_file.stem.replace("ak_index_global_hist_em_", "")
            for tc in FALLBACK_INDEX_SYMBOLS
        ):
            csvs.append(csv_file)

    # 获取 start date
    start_date = get_start_date(csvs)

    for csv_file in csvs:
        try:
            df_tmp = pd.read_csv(csv_file)

            if "日期" in df_tmp.columns and "今开" in df_tmp.columns:
                # 解析日期并归一化今开列
                # dates = pd.to_datetime(df_tmp["日期"], errors="coerce")
                dates = df_tmp["日期"]
                vals = pd.to_numeric(df_tmp["今开"], errors="coerce")
                if vals.dropna().empty:
                    continue

                # 计算norm
                start_val = vals[dates == start_date].values[0]
                norm = vals / start_val
                # norm(Series) 保留两位小数
                norm = norm.round(2)

                name = csv_file.stem.replace("ak_index_global_hist_em_", "")

                # 合并数据
                if "merged_df" in locals():
                    merged_df = pd.merge(
                        merged_df,
                        pd.DataFrame({"日期": dates, name: norm}),
                        on="日期",
                        how="outer",
                    )
                else:
                    merged_df = pd.DataFrame({"日期": dates, name: norm})

        except Exception as e:
            logger.error(f"读取文件 {csv_file} 失败: {e}")

    # 保存合并后的数据
    if "merged_df" in locals():
        merged_df.sort_values("日期", inplace=True)
        merge_file = output_dir / f"ak_index_global_merged_{start_date}.csv"
        merged_df.to_csv(merge_file, index=False)
        logger.info(f"全球指数合并数据已保存: {merge_file}")
    else:
        logger.error("没有可合并的全球指数数据")


def get_start_date(csvs: list) -> str:
    """
    获取多个csv文件的共同起始日期, 非连续
    """
    k = "日期"
    common_dates = set(pd.read_csv(csvs[0])[k])
    for f in csvs[1:]:
        common_dates &= set(pd.read_csv(f)[k])
    common_dates = sorted(list(common_dates))

    if common_dates:
        return min(common_dates)


def get_ak_macro_data():
    """获取 akshare 宏观经济数据"""
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


def get_ak_cpi_data():

    # date_str = datetime.now().strftime('%Y%m%d')

    # cpi消费者物价指数
    cpi_cn_data = safe_call(ak.macro_china_cpi_yearly)
    if cpi_cn_data is not None:
        filename = f"datas/raw/cpis/macro_china_cpi_yearly.csv"
        ensure_dir(filename)
        cpi_cn_data.to_csv(filename, index=False)
        logger.info(f"中国CPI数据: {filename} 已更新")

    # cpi 美国
    cpi_usa = safe_call(ak.macro_usa_cpi_yoy)
    if cpi_usa is not None:
        filename = f"datas/raw/cpis/macro_usa_cpi_yoy.csv"
        ensure_dir(filename)
        cpi_usa.to_csv(filename, index=False)
        logger.info(f"美国CPI数据: {filename} 已更新")
    # cpi 欧元区
    cpi_enro = safe_call(ak.macro_euro_cpi_yoy)
    if cpi_enro is not None:
        filename = f"datas/raw/cpis/macro_euro_cpi_yoy.csv"
        ensure_dir(filename)
        cpi_enro.to_csv(filename, index=False)
        logger.info(f"欧元区CPI数据: {filename} 已更新")

    # cpi 澳大利亚
    cpi_australia = safe_call(ak.macro_australia_cpi_yearly)
    if cpi_australia is not None:
        filename = f"datas/raw/cpis/macro_australia_cpi_yearly.csv"
        ensure_dir(filename)
        cpi_australia.to_csv(filename, index=False)
        logger.info(f"澳大利亚CPI数据: {filename} 已更新")

    # cpi 加拿大
    cpi_canada = safe_call(ak.macro_canada_cpi_yearly)
    if cpi_canada is not None:
        filename = f"datas/raw/cpis/macro_canada_cpi_yearly.csv"
        ensure_dir(filename)
        cpi_canada.to_csv(filename, index=False)
        logger.info(f"加拿大CPI数据: {filename} 已更新")

    # cpi 日本
    cpi_japan = safe_call(ak.macro_japan_cpi_yearly)
    if cpi_japan is not None:
        filename = f"datas/raw/cpis/macro_japan_cpi_yearly.csv"
        ensure_dir(filename)
        cpi_japan.to_csv(filename, index=False)
        logger.info(f"日本CPI数据: {filename} 已更新")


def get_ak_gdp_data():

    # date_str = datetime.now().strftime('%Y%m%d')
    # china gdp
    china_gdp = safe_call(ak.macro_china_gdp_yearly)
    if china_gdp is not None:
        filename = f"datas/raw/gdps/ak_china_gdp.csv"
        ensure_dir(filename)
        china_gdp.to_csv(filename, index=False)
        logger.info(f"中国GDP数据: {filename} 已更新")

    # usa gdp
    usa_gdp = safe_call(ak.macro_usa_gdp_monthly)
    if usa_gdp is not None:
        filename = f"datas/raw/gdps/ak_usa_gdp.csv"
        ensure_dir(filename)
        usa_gdp.to_csv(filename, index=False)
        logger.info(f"美国GDP数据: {filename} 已更新")

    # euro gdp
    enro_gdp = safe_call(ak.macro_euro_gdp_yoy)
    if enro_gdp is not None:
        filename = f"datas/raw/gdps/ak_euro_gdp.csv"
        ensure_dir(filename)
        enro_gdp.to_csv(filename, index=False)
        logger.info(f"欧元区GDP数据: {filename} 已更新")

    # canada gdp
    canada_gdp = safe_call(ak.macro_canada_gdp_monthly)
    if canada_gdp is not None:
        filename = f"datas/raw/gdps/ak_canada_gdp.csv"
        ensure_dir(filename)
        canada_gdp.to_csv(filename, index=False)
        logger.info(f"加拿大GDP数据: {filename} 已更新")


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


def update_weekly():
    """低频数据：REITs / 全球指数历史 + 合并 / 宏观 / 静态列表 / 标准口径 GDP-CPI

    注: 这些数据发布频率本身就是月度/季度, 且逐个抓历史容易被限流,
        建议每周或每月跑一次。
    """
    get_ak_reits_data()
    merge_ak_reits()
    get_ak_index_global_data()
    merge_ak_index()
    get_ak_macro_data()
    build_std_gdp()
    build_std_cpi()
    get_ak_stock_data()


if __name__ == "__main__":
    from utils.set_log import set_log

    set_log("update_weekly.log")
    update_weekly()
