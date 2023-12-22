from datetime import datetime, timedelta

import pandas as pd


# TODO: 定期更新数据


# TODO: 展示表格

def common_logic():
    df = pd.read_csv('datas/bonds/conv_20231220.csv')

    # 去掉未来半年到期的
    df['到期时间'] = pd.to_datetime(df['到期时间'])
    half_year = datetime.now() + timedelta(days=365//2)
    df = df[df['到期时间'] > half_year]

    # ST 有退市风险
    df = df[~df['正股名称'].str.contains(r'ST|\*')]

    # TODO: 不买银行的
    return df
    # df.sort_values(by=['现价', '转股价值', '转股溢价率'], ascending=[True, False, True])


def double_common_logic():
    df = common_logic()
    df = df[df['双低'] < 125]
    return df


def get_double_low(num: int = 30):
    """
    双低
    """
    df = double_common_logic()
    df = df.sort_values(by=['双低'], ascending=[True]).head(num)
    return df


def get_double_low_and_low_premium_rate(num: int = 30):
    """
    双低, 低溢价率
    """
    df = double_common_logic()
    df = df.sort_values(by=['转股溢价率'], ascending=[True]).head(num)
    return df


def get_low_premium_rate_and_double_low(num: int = 30):
    """
    低溢价率, 双低
    """
    df = common_logic()
    df = df.sort_values(by=['转股溢价率'], ascending=[True]).head(40)
    df = df.sort_values(by=['双低'], ascending=[True]).head(num)

    return df


def get_final_list():
    """
    最终名单
    """
    df1 = get_double_low()
    df2 = get_double_low_and_low_premium_rate()
    df3 = get_low_premium_rate_and_double_low()
    final_df = df1.merge(df2).merge(df3)

    final_df = final_df.sort_values(by=['转股价值'], ascending=[False])
    return final_df


if __name__ == '__main__':
    df = get_final_list()
    print(df)
    # breakpoint()
