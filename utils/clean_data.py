from pathlib import Path

from loguru import logger
import pandas as pd

from .constants import *


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
        df = convert_time(df, target_columns[0])
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


def clean_one_index(new_csv: str, target_new_columns: dict, usd_rate: float) -> pd.DataFrame:
    # {'日期':'date', '收盘':'MSCI印度指数'}

    df = pd.read_csv(new_csv)
    df.rename(columns=target_new_columns, inplace=True)
    target_columns = list(target_new_columns.values())

    df = convert_time(df, target_columns[0])

    # 转为object
    # df['date'].apply(lambda x: x.strftime('%Y-%m-%d'))
    # df[target_columns[0]] = df[target_columns[0]].astype('object')

    valid_df = df[target_columns]
    if pd.api.types.is_string_dtype(valid_df[target_columns[1]]):
        valid_df[target_columns[1]] = valid_df[target_columns[1]].str.replace(',', '')
        valid_df[target_columns[1]] = valid_df[target_columns[1]].astype(float)

    valid_df[target_columns[1]] *= usd_rate

    return valid_df


def update_one(old_all_csv: str, new_csv: str, target_new_columns: dict, output_csv: str):
    old_all_df = pd.read_csv(old_all_csv)
    old_all_df = convert_time(old_all_df, 'date')

    df = clean_one_index(new_csv, target_new_columns, 0.012)
    df_m = pd.merge(old_all_df, df, how='outer', on='date')

    df_m.sort_values('date', inplace=True)

    print(df_m.dtypes)
    df_m.to_csv(output_csv, index=False)
    return output_csv


def convert_time(df, target_column: str):
    try:
        df[target_column] = pd.to_datetime(df[target_column])
    except:
        df[target_column] = pd.to_datetime(df[target_column], format='%Y年%m月')
    return df




# clean_one_index('datas/indexes/MSCI印度指数历史数据.csv', ["日期", "收盘"])
# update_one(
#     'datas/indexes/all_indexes_data_usd.csv',
#     'datas/indexes/MSCI印度指数历史数据.csv',
#     {'日期': 'date', '收盘': 'MSCI印度指数'},
#     'datas/indexes/all_indexes_data_usd2.csv'
# )
