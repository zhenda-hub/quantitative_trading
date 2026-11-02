from pathlib import Path

import pandas as pd
from loguru import logger


def convert_time(df: pd.DataFrame, target_column: str) -> pd.DataFrame:
    """把时间列转换成 datetime

    兼容源文件两种写法: '2025-09-17' 与 '2025年09月'

    Args:
        df: 待处理的 DataFrame
        target_column: 时间列名

    Returns:
        DataFrame(原地修改并返回)
    """
    raw = df[target_column].astype(str)
    parsed = pd.to_datetime(raw, errors="coerce")
    missing = parsed.isna()
    if missing.any():
        parsed[missing] = pd.to_datetime(
            raw[missing], format="%Y年%m月", errors="coerce"
        )
    df[target_column] = parsed
    return df


def merge_res(
    csv_paths: list,
    target_columns: list,
    new_columns: list,
    output_csv: str,
    column_aliases: dict = None,
):
    """
    按照时间, 合并多种类型的csv为一个csv
    Args:
        csv_paths: 待合并的 csv 路径列表
        target_columns: 目标列; 第一列必须是时间, 会转成 datetime 并排序
        new_columns: 输出 csv 的列名
        output_csv: 输出路径
        column_aliases: 兼容源文件表头变化, 形如
            {'时间': ['时间', '日期'], '现值': ['现值', '今值']}

    Returns:
        输出路径
    """

    def _read_and_align(csv_path, value_name):
        df = pd.read_csv(csv_path)
        if column_aliases:
            rename = {}
            for canonical, candidates in column_aliases.items():
                if canonical in df.columns:
                    continue
                for candidate in candidates:
                    if candidate in df.columns:
                        rename[candidate] = canonical
                        break
            if rename:
                df = df.rename(columns=rename)
                logger.debug(f"{csv_path} 列名已归一: {rename}")
        lacking = [c for c in target_columns if c not in df.columns]
        if lacking:
            raise KeyError(
                f"{csv_path} 缺少列 {lacking}, 实际列为 {list(df.columns)}"
            )
        df = convert_time(df, target_columns[0])[target_columns]
        # 先改成最终列名, 避免多次 merge 时同名量列被自动加后缀
        return df.rename(
            columns={target_columns[0]: new_columns[0], target_columns[1]: value_name}
        )

    if len(new_columns) != len(csv_paths) + 1:
        raise ValueError(
            f"new_columns 数量 {len(new_columns)} 与 {len(csv_paths)} 个文件不匹配"
        )

    frames = [
        _read_and_align(path, new_columns[i + 1]) for i, path in enumerate(csv_paths)
    ]

    df_m = frames[0]
    for frame in frames[1:]:
        df_m = df_m.merge(frame, how="outer", on=new_columns[0])

    df_m.sort_values(new_columns[0], inplace=True)

    df_m.to_csv(output_csv, index=False)
    logger.info(f"{output_csv}已更新, 共 {len(df_m)} 行")
    return output_csv
