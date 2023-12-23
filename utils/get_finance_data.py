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

    'HSI': "香港恒生指数",  # * 0.128 = 美元

    '000001': "中国上证指数",  # *0.145=美元
    '399001': "中国深证指数",
    '000300': "沪深300指数",
    '000016': "上证50",
    '000905': "中证500",
    '000015': "上证红利",
    '000922': "中证红利",

    '日经225指数历史数据': "日经225指数",  # *0.008=美元
    '韩国KOSPI指数历史数据': "韩国KOSPI指数",  # *0.0008=美元

    'MSCI新加坡指数历史数据': "MSCI新加坡指数",  # *1.36=美元
    'MSCI加拿大指数历史数据': "MSCI加拿大指数",  # *0.76=美元

    'MSCI欧盟指数历史数据': "MSCI欧盟指数",  # *1.1=美元
}

VIRTUAL_SYMBOL_NAME_DICT = {
    'BTC': "比特币",
    'ETH': "以太坊",
    'USDT': "泰达币",
    'XRP': "XRP",
    'BNB': "BNB",
    'SOL': "Solana",
}

CPI_NAME_FILE_DICT = {
    'australia': "macro_australia_cpi_yearly.csv",
    'canada': "macro_canada_cpi_yearly.csv",
    'china': "macro_china_cpi_yearly.csv",
    'euro': "macro_euro_cpi_yoy.csv",
    'japan': "macro_japan_cpi_yearly.csv",
    'usa': "macro_usa_cpi_yoy.csv",
}

UNEMP_NAME_FILE_DICT = {
    'australia': "australia_unemps.csv",
    'canada': "canada_unemps.csv",
    'china': "china_unemps.csv",
    'euro': "euro_unemps.csv",
    'japan': "japan_unemps.csv",
    'usa': "usa_unemps.csv",
}

GDP_NAME_FILE_DICT = {
    'china': "china_gdp.csv",
    'euro': "euro_gdp.csv",
    'usa': "usa_gdp.csv",
}

PERIOD_ACTION = {
    '上升': ['持续买股票'],
    '高点': ['卖出股票', '买债券，黄金'],
    '下降': ['买债券，黄金', '不碰股票'],
    '低点': ['买股票', '卖债券，黄金'],
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
#         ak.crypto_hist  # 虚拟货币历史NG
#         'https://cn.investing.com/crypto/currencies'  # 虚拟货币url

        # gdp
        # ak.macro_china_gdp_yearly,  # gdp
        # ak.macro_china_gdp,  # gdp
        # ak.macro_china_hk_gbp()  # FIXME: not work
        # ak.macro_usa_gdp_monthly()  # usa gdp
        # ak.macro_euro_gdp_yoy()  # euro gdp

        # unemp
        # ak.macro_china_urban_unemployment,  # china
        # ak.macro_china_hk_rate_of_unemployment, # hk unemp FIXME: not work
        # ak.macro_usa_unemployment_rate, # usa unemp
        # ak.macro_euro_unemployment_rate_mom,  # euro
        # ak.macro_japan_unemployment_rate,  # japan
        # ak.macro_australia_unemployment_rate,  # australia
        # ak.macro_canada_unemployment_rate,  # canada

        # ak.macro_china_pmi_yearly, # pmi(宏观经济好不好)
        # ak.macro_china_money_supply,  # 中国货币供应量
        # # ppi生产者物价指数(生产成本)

        # cpi
        # ak.macro_china_cpi_yearly,  # cpi消费者物价指数
        # ak.macro_usa_cpi_yoy,  # cpi 美国
        # ak.macro_euro_cpi_yoy,  # cpi 欧元区
        # ak.macro_australia_cpi_yearly,
        # ak.macro_canada_cpi_yearly,
        # ak.macro_japan_cpi_yearly,


        # 可转债
        # ak.bond_zh_cov_value_analysis,  # 可转债价值分析
#         ak.bond_zh_us_rate,  # 国债收益率

        # ak.fund_portfolio_hold_em,  # 基金持仓
        # ak.fund_portfolio_industry_allocation_em,  # 基金行业配置
        # ak.fund_report_industry_allocation_cninfo,  # 基金行业配置2
#
#
#         ak.stock_zh_index_spot,  # 大盘指数
#         ak.stock_zh_index_daily,  # 大盘指数
#         # ak.reits_realtime_em,  # reits
#         # ak.index_value_name_funddb,  # 指数
#         ak.stock_a_ttm_lyr,  # 中位数市盈率
#         ak.fund_aum_hist_em,  # 基金规模
#         ak.fund_report_industry_allocation_cninfo,  # 基金行业配置
#         ak.google_index,  # 谷歌指数
#         ak.fund_aum_em,
#     ],
#     # 行业 窄基, 看5年即可
#     'narrow_base': [
#         ak.stock_fund_flow_industry
#         ak.stock_sector_fund_flow_hist,
#         ak.fund_fh_rank_em,  # 分红排行榜， FIXME: not work

#         ak.stock_board_concept_name_ths,  # 概念板块-名称， 容易炒作
#         ak.stock_board_concept_info_ths,  # 概念板块-板块简介

        # ak.stock_board_industry_name_em,  # 行业板块-名称， 推荐
        # ak.stock_board_industry_cons_em,  # 东财行业成分股， 推荐
#         ak.stock_board_industry_summary_ths,  # 同花顺行业一览表

#         ak.stock_board_cons_ths,  #  同花顺行业成分股， FIXME: not work

        # ak.stock_board_industry_info_ths,  # 行业板块-板块简介, 信息很少，没用
#         ak.stock_board_industry_index_ths,  # 行业指数

#         ak.stock_industry_pe_ratio_cninfo,  # 行业市盈率
#         ak.stock_classify_sina,  # 按 symbol 分类后的股票
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


def merge_indexes():
    base_path = Path('datas/indexes')
    csv_paths = [base_path / f'{k}.csv' for k in MAIN_INDEX_SYMBOL_NAME_DICT]

    new_columns = list(MAIN_INDEX_SYMBOL_NAME_DICT.values())
    new_columns.insert(0, 'date')
    # target_columns = ['date', 'close']
    target_columns = ["日期", "收盘"]
    addr = merge_res(csv_paths, target_columns, new_columns, 'datas/indexes/all_indexes_data.csv')
    print('addr:', addr)


def merge_virtuals():
    base_path = Path('datas/virtual')
    csv_paths = [base_path / f'{v}历史数据.csv' for v in VIRTUAL_SYMBOL_NAME_DICT.values()]

    new_columns = list(VIRTUAL_SYMBOL_NAME_DICT.values())
    new_columns.insert(0, 'date')
    target_columns = ['date', 'close']

    addr = merge_res(csv_paths, target_columns, new_columns, 'datas/virtual/all_virtual_data.csv')
    print('addr:', addr)


def merge_cpis():
    """
    消费者物价指数年率
    """
    base_path = Path('datas/cpis')
    csv_paths = [base_path / v for v in CPI_NAME_FILE_DICT.values()]

    new_columns = list(CPI_NAME_FILE_DICT.keys())
    new_columns.insert(0, 'date')

    target_columns = ['时间', '现值']
    breakpoint()
    addr = merge_res(csv_paths, target_columns, new_columns, 'datas/cpis/all_cpi_data.csv')
    print('addr:', addr)


def merge_unemps():
    """
    失业率
    """
    base_path = Path('datas/unemps')
    csv_paths = [base_path / v for v in UNEMP_NAME_FILE_DICT.values()]

    new_columns = list(UNEMP_NAME_FILE_DICT.keys())
    new_columns.insert(0, 'date')

    target_columns = ['时间', '现值']
    # breakpoint()
    addr = merge_res(csv_paths, target_columns, new_columns, 'datas/unemps/all_unemps_data.csv')
    print('addr:', addr)


def merge_gdps():
    """
    GDP
    """
    base_path = Path('datas/gdps')
    csv_paths = [base_path / v for v in GDP_NAME_FILE_DICT.values()]

    new_columns = list(GDP_NAME_FILE_DICT.keys())
    new_columns.insert(0, 'date')

    target_columns = ['日期', '今值']
    # breakpoint()
    addr = merge_res(csv_paths, target_columns, new_columns, 'datas/gdps/all_gdps_data.csv')
    print('addr:', addr)


def merge_res(csv_paths: list, target_columns: list, new_columns: list, output_csv: str):
    """

    Args:
        csv_paths:
        target_columns: first must be time , will convert to datetime, sorted
        new_columns:
        output_csv:

    Returns:

    """

    df_list = [pd.read_csv(csv_path) for csv_path in csv_paths]
    df_list_target = []  # target df
    for df in df_list:
        # if '日期' in df.columns:
        #     df.rename(columns={'日期': 'date', '收盘': 'close'}, inplace=True)
        # breakpoint()
        try:
            df[target_columns[0]] = pd.to_datetime(df[target_columns[0]])
        except:
            df[target_columns[0]] = pd.to_datetime(df[target_columns[0]], format='%Y年%m月')
        df_list_target.append(df[target_columns])
    breakpoint()
    df_m = pd.merge(df_list_target[0], df_list_target[1], how='outer', on=target_columns[0])
    for i, df in enumerate(df_list_target[2:]):
        df_m = df_m.merge(df, how='outer', on=target_columns[0], suffixes=(f'_{i}', f'_{i+1}'))

    df_m.columns = new_columns


    df_m.sort_values('date', inplace=True)

    print(df_m.dtypes)
    breakpoint()
    # df_m['比特币'] = df_m['比特币'].str.replace(',', '')
    # df_m['比特币'] = df_m['比特币'].astype(float)
    # df_m['以太坊'] = df_m['以太坊'].str.replace(',', '')
    # df_m['以太坊'] = df_m['以太坊'].astype(float)
    # pd.to_numeric()
    df_m.to_csv(output_csv, index=False)
    return output_csv


def get_top_industries():
    pass


def get_top_3_by_industry(industry: str):
    pass


def get_other_indexes():
    # 下载日经225指数数据
    nikkei = yf.Ticker("^N225")

    # 获取历史数据时间范围
    hist = nikkei.history(start="2010-01-01", end="2023-02-28")  # FIXME: not work

    # 将数据转换为DataFrame
    df = pd.DataFrame(hist)
    breakpoint()


def get_datas_from_url(url: str):
    df = pd.read_html(url)
    breakpoint()


def get_period(unemp_month_on_month: float, cpi_month_on_month: float, threshold=0.05):
    print(f'unemp: {unemp_month_on_month}， cpi： {cpi_month_on_month}')

    if unemp_month_on_month > 0 and cpi_month_on_month > 0:
        if unemp_month_on_month > threshold and cpi_month_on_month > threshold:
            return '上升'
        else:
            return '高点'
    if unemp_month_on_month < 0 and cpi_month_on_month < 0:
        if abs(unemp_month_on_month) > threshold and abs(cpi_month_on_month) > threshold:
            return '下降'
        else:
            return '低点'

    return '未知'


def get_bond():
    # get_datas_from_url('https://app.jisilu.cn/web/data/cb/list')
    # df = ak.bond_cb_jsl(cookie="kbzw__Session=s81b1un9m9187t896kt8mlg1c2; Hm_lvt_164fe01b1433a19b507595a43bf58262=1703006843; kbz_newcookie=1; kbzw__user_login=7Obd08_P1ebax9aX8dzaz9mYrqXR0dTn8OTb3crUjaiU2tqqqJTUmdms1p7bod2a2sSn2NmtkqCY2q7Zmt-dmJ2j1uDb0dWMoZWqsa2hrI2yj7e11dSeqZiglKSprJ6uopido7a41dCjrt_b3eXhyqihpZKWic7g4dzQ59SUx8mJqpylkrGBzuDhrpWrgeyvqZKZrefS4sbO3NXDyuSQqaysl6yil4rBqcvEv6SB3Mrf3pWw3s_i0Z-But_l587VkKWrpZepmqeQpoHK2NnZ09mQqaysl6yil6fayKaopaiPoI-kp6U.; Hm_lpvt_164fe01b1433a19b507595a43bf58262=1703008180; SERVERID=0e73f01634e37a9af0b56dfcd9143ef3|1703008222|1703006836")
    df = ak.bond_cb_jsl(cookie="kbzw__Session=s81b1un9m9187t896kt8mlg1c2; Hm_lvt_164fe01b1433a19b507595a43bf58262=1703006843; kbz_newcookie=1; kbzw__user_login=7Obd08_P1ebax9aX8dzaz9mYrqXR0dTn8OTb3crUjaiU2tqqqJTUmdms1p7bod2a2sSn2NmtkqCY2q7Zmt-dmJ2j1uDb0dWMoZWqsa2hrI2yj7e11dSeqZiglKSprJ6uopido7a41dCjrt_b3eXhyqihpZKWic7g4dzQ59SUx8mJqpylkrGBzuDhrpWrgeyvqZKZrefS4sbO3NXDyuSQqaysl6yil4rBqcvEv6SB3Mrf3pWw3s_i0Z-But_l587VkKWrpZepmqeQpoHK2NnZ09mQqaysl6yil6fayKaopaiPoI-kp6U.; kbz__Session=3ktlma07vpd2kan6ss1si7e5a2; kbz__user_login=1ubd08_P1ebax9aX8dzaz9WZnJ3R1ezo4Oje28DTjKWrxNOYpKzZod6f2JfYltmwxdOR1d-qmqmj3ZfaktmpgquO6eLZx9aXqJasmauwlJGcobrJx9aXqJmmlKask6KXppqwls6t1b-hruLyytzN1aiql6mMn7nfz9fn2OOBws2Vmqmap52WuNzml6SclPGrnaKMuNLmzdjPxtKs3e2knqyjpZWsgZvDqcSuwKWV1eLX3IK9xtbj0JmBt-Hn2ObRppOokaGoj6CPpJnIyt_N6cullqavj6OXlL7Z0KidqZKkkaGoj6A.; Hm_lpvt_164fe01b1433a19b507595a43bf58262=1703342263; SERVERID=5452564f5a1004697d0be99a0a2e3803|1703342408|1703338327")
    breakpoint()
    df.to_csv(f'datas/bonds/conv_{datetime.datetime.now().strftime("%Y%m%d")}.csv', index=False)


# df2 = ak.bond_cb_redeem_jsl()  # 强赎df
# ak.bond_zh_cov()  # 申购债券


if __name__ == '__main__':
    # merge_virtuals()
    # merge_cpis()
    # merge_indexes()
    # merge_unemps()
    # merge_gdps()
    # get_bond()
    breakpoint()
    # ak.stock_board_industry_info_ths
    # pd.DataFrame().sort_values()

    # ak.index_investing_global_from_url('https://www.investing.com/indices/germany-30-futures', end_date='20550102')
    # ak.index_investing_global(area="德国", symbol ="德国DAX30指数", period ="每日", start_date ="20050101", end_date ="20550605")

    # df['Date'] = df['Date'].map(lambda x: x.strftime('%Y-%m-%d'))


    # merge_indexes()
