import datetime
import time
import pdb
from pathlib import Path

import pandas as pd
from pandas_datareader import data
import yfinance as yf  # 国际
import akshare as ak  # 国内
import easyquotation


MAIN_INDEX_SYMBOL_NAME_DICT = {
    'INX': "标普500指数",
    'DJI':  "道琼斯工业平均指数",
    'IXIC': "纳斯达克综合指数",

    'HSI': "香港恒生指数",

    '000001': "中国上证指数",
    '399001': "中国深证指数",
    '000300': "沪深300指数",
    '000016': "上证50",
    '000905': "中证500",
    '000015': "上证红利",
    '000922': "中证红利",

    # '^N225': "日经225",
    # '^KS11': "韩国KOSPI",
    # '^STI': "富时新加波",
    # '^GDAXI': "德国DAX30",
    # '^FTSE': "英国富时100",
    # '^TSX': "加拿大",
}


# funcs = {
#     # 大盘 宽基
#     'wide_base': [
#         ak.fund_etf_hist_em,
#         ak.index_zh_a_hist,  # A股指数
#
        # ak.index_us_stock_sina(symbol=".INX"),  # 美国指数
#
#         ak.stock_hk_index_spot_em(),
#         ak.stock_hk_index_daily_em(symbol="HSI"),  # 恒生指数
#
#         ak.fund_portfolio_hold_em,  # 基金持仓1
#         ak.fund_portfolio_industry_allocation_em,  # 基金持仓2
#
#         ak.crypto_hist,  # 虚拟货币
#
#         ak.stock_zh_index_spot,  # 大盘指数
#         ak.stock_zh_index_daily,  # 大盘指数
#         # ak.reits_realtime_em,  # reits
#         # ak.index_value_name_funddb,  # 指数
#         ak.bond_zh_us_rate,  # 国债收益率
#         ak.stock_a_ttm_lyr,  # 中位数市盈率
#         ak.fund_aum_hist_em,  # 基金规模
#         ak.fund_report_industry_allocation_cninfo,  # 基金行业配置
#         ak.google_index,  # 谷歌指数
#         ak.fund_aum_em,
#     ],
#     # 行业 窄基
#     'narrow_base': [
#         ak.stock_board_concept_name_ths,  # 概念板块-名称
#         ak.stock_board_industry_name_em,  # 行业板块-名称
#         ak.stock_board_industry_info_ths,  # 行业板块-板块简介
#         ak.stock_board_concept_info_ths,  # 概念板块-板块简介
#         ak.stock_industry_pe_ratio_cninfo,  # 行业市盈率
#         ak.stock_classify_sina,  # 按 symbol 分类后的股票
#         ak.stock_board_industry_summary_ths,  # 同花顺行业一览表
#     ],
#     'stocks': [
#         # 个股
#         ak.stock_a_indicator_lg,  # 市盈率, 市净率, 股息率数据接口
#         ak.stock_index_pe_lg(indicator="pe_ttm"),  # 指数市盈率
#         ak.stock_market_pe_lg(indicator="pe_ttm"),  # 市场市盈率
#         # ak.stock_info_a_code_name,  # 所有股票代码
#         # # 港股
#         # ak.stock_zh_ah_daily,  # 港股历史行情
#         # ak.stock_zh_ah_spot,  # 港股实时行情
#         # # A股
#         # ak.stock_zh_a_spot,  # 实时数据
#         # ak.stock_zh_a_daily,  # 个股历史数据
#         # ak.stock_zh_a_cdr_daily,  # 个股历史cdr数据
#         # ak.stock_zh_a_minute,  # 个股历史min数据
#     ],
#     'stocks_info': [
#         ak.stock_balance_sheet_by_yearly_em,  # 资产负债表-按年度
#         ak.stock_profit_sheet_by_yearly_em,  # 利润表-按年度
#         ak.stock_cash_flow_sheet_by_yearly_em,  # 现金流量表-按年度
#
#         ak.stock_a_ttm_lyr(),  # 中位数市盈率
#         ak.stock_dividents_cninfo,  # 个股分红
#         ak.stock_individual_info_em,  # 个股信息
#         ak.stock_profile_cninfo,  # 个股-公司概况
#
#         # 收益率roe。。。
#         ak.stock_us_famous_spot_em,  # 知名美股
#     ],
# }


def get_maotai():
    # 定义起始日期和结束日期
    datetime.datetime()

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


# def get_index_ak():
#     for func in funcs['wide_base']:
#         df = func()
#         pdb.set_trace()
#         time.sleep(2)
#
#
# def get_stock_ak():
#     for func in funcs['stocks']:
#         df = func()
#         pdb.set_trace()
#         time.sleep(2)


def merge_indexes():
    indexes_path = Path('datas/indexes')
    csv_paths = [indexes_path / f'{k}.csv' for k in MAIN_INDEX_SYMBOL_NAME_DICT]
    df_list = [pd.read_csv(csv_path) for csv_path in csv_paths]
    df_list_close = []
    for df in df_list:
        if '日期' in df.columns:
            df.rename(columns={'日期': 'date', '收盘': 'close'}, inplace=True)
        df_list_close.append(df[['date', 'close']])


    new_columns = list(MAIN_INDEX_SYMBOL_NAME_DICT.values())
    new_columns.insert(0, 'date')
    # breakpoint()

    df_m = pd.merge(df_list_close[0], df_list_close[1], how='outer', on='date')
    for i, df in enumerate(df_list_close[2:]):
        df_m = df_m.merge(df, how='outer', on='date', suffixes=(f'_{i}', f'_{i+1}'))

    df_m.columns = new_columns
    df_m.sort_values('date', inplace=True)
    breakpoint()
    df_m.to_csv('datas/indexes/all_indexes_data.csv', index=False)


def get_industries():
    pass


def get_top_10_by_industry(industry: str):
    pass


def get_other_indexes():
    # 下载日经225指数数据
    nikkei = yf.Ticker("^N225")

    # 获取历史数据时间范围
    hist = nikkei.history(start="2010-01-01", end="2023-02-28")

    # 将数据转换为DataFrame
    df = pd.DataFrame(hist)


if __name__ == '__main__':
    breakpoint()
    # ak.index_investing_global_from_url('https://www.investing.com/indices/germany-30-futures', end_date='20550102')
    # ak.index_investing_global(area="德国", symbol ="德国DAX30指数", period ="每日", start_date ="20050101", end_date ="20550605")

    # df['Date'] = df['Date'].map(lambda x: x.strftime('%Y-%m-%d'))


    merge_indexes()
