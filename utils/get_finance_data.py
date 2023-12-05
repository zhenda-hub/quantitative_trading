import datetime
import time
import pdb

import pandas as pd
import yfinance as yf  # 国际
import akshare as ak  # 国内
import easyquotation


def get_maotai():
    # 定义起始日期和结束日期
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


def get_every_type_ak():
    # FIXME
    # df = ak.stock_zcfz_em('20230425')  # 资产负债表
    # df2 = ak.stock_lrb_em('20230425')  # 利润表
    # df3 = ak.stock_xjll_em('20230425')  # 现金流量表
    funcs = [

        # 大盘 宽基
        ak.stock_zh_index_spot,  # 大盘指数
        ak.stock_zh_index_daily,  # 大盘指数
        # ak.reits_realtime_em,  # reits
        # ak.index_value_name_funddb,  # 指数
        ak.bond_zh_us_rate,  # 国债收益率
        ak.stock_a_ttm_lyr,  # 中位数市盈率
        ak.fund_aum_hist_em,  # 基金规模
        ak.fund_report_industry_allocation_cninfo,  # 基金行业配置
        ak.google_index,  # 谷歌指数

        # 行业 窄基
        ak.stock_board_concept_name_ths,  # 概念板块-名称
        ak.stock_board_industry_name_em,  # 行业板块-名称
        ak.stock_board_industry_info_ths,  # 行业板块-板块简介
        ak.stock_board_concept_info_ths,  # 概念板块-板块简介
        ak.stock_industry_pe_ratio_cninfo,  # 行业市盈率
        ak.stock_classify_sina,  # 按 symbol 分类后的股票
        ak.stock_board_industry_summary_ths,  # 同花顺行业一览表

        # 个股
        ak.stock_a_indicator_lg,  # 市盈率, 市净率, 股息率数据接口
        ak.stock_index_pe_lg(indicator="pe_ttm"),  # 指数市盈率
        ak.stock_market_pe_lg(indicator="pe_ttm"),  # 市场市盈率
        # ak.stock_info_a_code_name,  # 所有股票代码
        # # 港股
        # ak.stock_zh_ah_daily,  # 港股历史行情
        # ak.stock_zh_ah_spot,  # 港股实时行情
        # # A股
        # ak.stock_zh_a_spot,  # 实时数据
        # ak.stock_zh_a_daily,  # 个股历史数据
        # ak.stock_zh_a_cdr_daily,  # 个股历史cdr数据
        # ak.stock_zh_a_minute,  # 个股历史min数据

        ak.stock_balance_sheet_by_yearly_em,  # 资产负债表-按年度
        ak.stock_profit_sheet_by_yearly_em,  # 利润表-按年度
        ak.stock_cash_flow_sheet_by_yearly_em,  # 现金流量表-按年度

        ak.stock_a_ttm_lyr(),  # 中位数市盈率
        ak.stock_dividents_cninfo,  # 个股分红
        ak.stock_individual_info_em,  # 个股信息
        ak.stock_profile_cninfo,  # 个股-公司概况

        # 收益率roe。。。




        ak.stock_us_famous_spot_em,  # 知名美股
    ]
    for func in funcs:
        df = func()
        pdb.set_trace()
        time.sleep(2)


def get_cn_stock_ids():
    pass


def get_hk_stock_ids():
    pass


def get_usa_stock_ids():
    pass


def get_industry():
    pass


def get_top_10(industry: str):
    pass


