import akshare as ak  # 国内
import efinance as ef  # 国内
import easyquotation as eq  # 国内
# import yfinance as yf  # 国际


ak_funcs = {
    # 大盘 宽基
    'wide_base': [
        ak.fund_etf_hist_em,
        ak.index_zh_a_hist,  # A股指数

        ak.index_us_stock_sina(symbol=".INX"),  # 美国指数

        ak.stock_hk_index_spot_em(),
        ak.stock_hk_index_daily_em(symbol="HSI"),  # 恒生指数
        ak.crypto_hist,  # 虚拟货币历史NG
        # 'https://cn.investing.com/crypto/currencies'  # 虚拟货币url

        # gdp
        ak.macro_china_gdp_yearly,  # gdp
        ak.macro_china_gdp,  # gdp
        ak.macro_china_hk_gbp()  # FIXME: not work
        ak.macro_usa_gdp_monthly()  # usa gdp
        ak.macro_euro_gdp_yoy()  # euro gdp

        # unemp 失业率
        ak.macro_china_urban_unemployment,  # china
        ak.macro_china_hk_rate_of_unemployment, # hk unemp FIXME: not work
        ak.macro_usa_unemployment_rate, # usa unemp
        ak.macro_euro_unemployment_rate_mom,  # euro
        ak.macro_japan_unemployment_rate,  # japan
        ak.macro_australia_unemployment_rate,  # australia
        ak.macro_canada_unemployment_rate,  # canada

        ak.macro_china_pmi_yearly, # pmi(宏观经济好不好)
        ak.macro_china_money_supply,  # 中国货币供应量
        # ppi生产者物价指数(生产成本)

        # cpi
        ak.macro_china_cpi_yearly,  # cpi消费者物价指数
        ak.macro_usa_cpi_yoy,  # cpi 美国
        ak.macro_euro_cpi_yoy,  # cpi 欧元区
        ak.macro_australia_cpi_yearly,
        ak.macro_canada_cpi_yearly,
        ak.macro_japan_cpi_yearly,


        # 可转债
        ak.bond_zh_cov_value_analysis('113045'),  # 可转债价值分析
        ak.bond_zh_us_rate,  # 国债收益率

        ak.fund_portfolio_hold_em,  # 基金持仓
        ak.fund_portfolio_industry_allocation_em,  # 基金行业配置
        ak.fund_report_industry_allocation_cninfo,  # 基金行业配置2


        ak.stock_zh_index_spot,  # 大盘指数
        ak.stock_zh_index_daily,  # 大盘指数
        # ak.reits_realtime_em,  # reits
        # ak.index_value_name_funddb,  # 指数
        ak.stock_a_ttm_lyr,  # 中位数市盈率
        ak.fund_aum_hist_em,  # 基金规模
        ak.fund_report_industry_allocation_cninfo,  # 基金行业配置
        ak.google_index,  # 谷歌指数
        ak.fund_aum_em,
    ],
    # 行业 窄基, 看5年即可
    'narrow_base': [
        ak.stock_fund_flow_industry
        ak.stock_sector_fund_flow_hist,
        ak.fund_fh_rank_em,  # 分红排行榜， FIXME: not work

        ak.stock_board_concept_name_ths,  # 概念板块-名称， 容易炒作
        ak.stock_board_concept_info_ths,  # 概念板块-板块简介

        ak.stock_board_industry_name_em,  # 行业板块-名称， 推荐
        ak.stock_board_industry_cons_em,  # 东财行业成分股， 推荐
        ak.stock_board_industry_summary_ths,  # 同花顺行业一览表

        ak.stock_board_cons_ths,  #  同花顺行业成分股， FIXME: not work

        ak.stock_board_industry_info_ths,  # 行业板块-板块简介, 信息很少，没用
        ak.stock_board_industry_index_ths,  # 行业指数

        ak.stock_industry_pe_ratio_cninfo,  # 行业市盈率
        ak.stock_classify_sina,  # 按 symbol 分类后的股票
    ],
    'stocks': [
        # 个股
        ak.stock_a_indicator_lg,  # 市盈率, 市净率, 股息率数据接口
        ak.stock_index_pe_lg(indicator="pe_ttm"),  # 指数市盈率
        ak.stock_market_pe_lg(indicator="pe_ttm"),  # 市场市盈率
        ak.stock_info_a_code_name,  # 所有股票代码
        # 港股
        ak.stock_zh_ah_daily,  # 港股历史行情
        ak.stock_zh_ah_spot,  # 港股实时行情
        # A股
        ak.stock_zh_a_spot,  # 实时数据
        ak.stock_zh_a_daily,  # 个股历史数据
        ak.stock_zh_a_cdr_daily,  # 个股历史cdr数据
        ak.stock_zh_a_minute,  # 个股历史min数据
    ],
    'stocks_info': [
        ak.stock_balance_sheet_by_yearly_em,  # 资产负债表-按年度
        ak.stock_profit_sheet_by_yearly_em,  # 利润表-按年度
        ak.stock_cash_flow_sheet_by_yearly_em,  # 现金流量表-按年度

        ak.stock_a_ttm_lyr(),  # 中位数市盈率
        ak.stock_dividents_cninfo,  # 个股分红
        ak.stock_individual_info_em,  # 个股信息
        ak.stock_profile_cninfo,  # 个股-公司概况

        # 收益率roe。。。
        ak.stock_us_famous_spot_em,  # 知名美股
    ],
}


ef_funcs = {
    'stocks': [
        # ef.stock.get_realtime_quotes, # 实时行情数据
        ef.stock.get_base_info,       # 基本信息
        ef.stock.get_quote_history,   # 历史行情数据
        ef.stock.get_belong_board,    # 所属板块
    ],
    'funds': [
        # ef.fund.get_fund_codes,       # 基金列表
        # ef.fund.get_quote_history,    # 历史行情
        
        # ef.fund.get_base_info,        # 基金基本信息
        # ef.fund.get_pdf_reports,      # 基金公告
        # ef.fund.get_types_percentage, # 基金类型占比
        # ef.stock.get_members,         # 获取指数的成分股
    ],
    'bonds': [
        # ef.bond.get_all_base_info,    # 债券基本信息
        ef.bond.get_quote_history,    # 债券历史行情
    ]
}


eq_funcs = {
    # 'realtime': [
    #     eq.use("sina"),             # 新浪实时行情
    #     eq.use("qq"),               # QQ实时行情
    # ],
    # 'quotation': [
    #     eq.real(["000001"]),        # 获取指定股票实时行情
    # ]
}


yf_funcs = {
    # 'stocks': [
    #     yf.Ticker,                   # 股票代码对象
    #     yf.download,                 # 下载历史数据
    # ],
    # 'indexes': [
    #     yf.Ticker('^GSPC'),          # 标普500
    #     yf.Ticker('^IXIC'),          # 纳斯达克
    #     yf.Ticker('^DJI'),           # 道琼斯
    # ],
    # 'etfs': [
    #     yf.Ticker('SPY'),            # SPDR标普500ETF
    #     yf.Ticker('QQQ'),            # Invesco纳斯达克100ETF
    # ]
}
