"""巨潮（国证行业分类）行业市盈率：历史回填 + 增量更新

数据源：ak.stock_industry_pe_ratio_cninfo(symbol="国证行业分类", date=YYYYMMDD)
- 一次请求返回当天全部 ~293 个行业（4 级分类）
- 场外可回溯到约 2023-06；非交易日返回空表
- 单次约 0.36 秒，830 个交易日串行约 5 分钟

口径：静态市盈率（按上年年报净利润），与自算的东财动态 PE 不同，两套并存。

输出：datas/processed/n_indexes/industry_pe_cninfo.csv
     按 (日期, 行业编码) 去重，long 表

用法：
    python -m utils.industry_valuation_cninfo              # 回填 2023-06-01 至今
    python -m utils.industry_valuation_cninfo --latest     # 只抓最近 1 个交易日
"""
from __future__ import annotations

import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
from pathlib import Path

import akshare as ak
import pandas as pd
from loguru import logger

OUTPUT = Path("datas/processed/n_indexes/industry_pe_cninfo.csv")
BACKFILL_START = "2023-06-01"

WORKERS = 4          # 并发数
CALL_TIMEOUT = 40    # 单请求超时（秒）
RETRY = 2
FLUSH_EVERY = 200    # 每处理多少个交易日落盘一次（防止中途中断丢数据）

KEEP_COLUMNS = [
    "日期",
    "行业编码",
    "行业名称",
    "行业层级",
    "公司数量",
    "纳入计算公司数量",
    "总市值-静态",
    "净利润-静态",
    "静态市盈率-加权平均",
    "静态市盈率-中位数",
]


def _call_with_timeout(fn, timeout: int = CALL_TIMEOUT):
    """守护线程里执行，超时返回 (None, 'timeout')"""
    box = {}

    def worker():
        try:
            box["value"] = fn()
        except Exception as error:  # noqa: BLE001
            box["error"] = error

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    thread.join(timeout)
    if thread.is_alive():
        return None, "timeout"
    if "error" in box:
        return None, f"{type(box['error']).__name__}: {box['error']}"
    return box.get("value"), None


def fetch_one(day: str) -> pd.DataFrame | None:
    """抓某个交易日（YYYYMMDD）的全行业 PE，空数据返回 None"""
    data, error = _call_with_timeout(
        lambda: ak.stock_industry_pe_ratio_cninfo(symbol="国证行业分类", date=day)
    )
    if data is None or not len(data):
        return None
    df = data.copy()
    df["日期"] = f"{day[:4]}-{day[4:6]}-{day[6:]}"
    keep = [c for c in KEEP_COLUMNS if c in df.columns]
    return df[keep]


def load_history(path: Path = OUTPUT) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, dtype={"行业编码": str})


def save(rows: list[pd.DataFrame], path: Path = OUTPUT) -> pd.DataFrame:
    """与已有文件合并、按 (日期, 行业编码) 去重后落盘"""
    if not rows:
        return load_history(path)
    new = pd.concat(rows, ignore_index=True)
    new["行业编码"] = new["行业编码"].astype(str)
    history = load_history(path)
    merged = pd.concat([history, new], ignore_index=True) if len(history) else new
    merged = merged.drop_duplicates(subset=["日期", "行业编码"], keep="last")
    merged = merged.sort_values(["日期", "行业层级", "行业编码"])
    path.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(path, index=False, encoding="utf-8-sig")
    return merged


def trade_days(start: str, end: str) -> list[str]:
    cal = ak.tool_trade_date_hist_sina()
    cal["trade_date"] = pd.to_datetime(cal["trade_date"])
    days = cal[(cal["trade_date"] >= start) & (cal["trade_date"] <= end)]["trade_date"]
    return [d.strftime("%Y%m%d") for d in days]


def build(latest_only: bool = False, workers: int = WORKERS):
    history = load_history()
    done_days = set(history["日期"].astype(str)) if len(history) else set()

    if latest_only:
        today = date.today()
        # 取最近 5 个自然日内的交易日，避免周末/节假日空跑
        days = trade_days((today - timedelta(days=7)).isoformat(), today.isoformat())
        days = days[-1:]
        logger.info(f"增量模式：目标交易日 {days}")
    else:
        days = trade_days(BACKFILL_START, date.today().isoformat())
        pending = [d for d in days if f"{d[:4]}-{d[4:6]}-{d[6:]}" not in done_days]
        logger.info(
            f"回填模式：{days[0]} ~ {days[-1]} 共 {len(days)} 个交易日，"
            f"已有 {len(days) - len(pending)} 天，待抓 {len(pending)} 天"
        )
        days = pending

    if not days:
        logger.info("没有需要更新的交易日")
        return history

    rows, failed, empty = [], [], []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(fetch_one, day): day for day in days}
        for index, future in enumerate(as_completed(futures), start=1):
            day = futures[future]
            try:
                df = future.result()
            except Exception as error:  # noqa: BLE001
                failed.append(day)
                logger.warning(f"[{day}] 异常: {error}")
                continue
            if df is None:
                empty.append(day)
                continue
            rows.append(df)
            if index % 50 == 0:
                logger.info(f"进度 {index}/{len(days)}，成功 {len(rows)}，空 {len(empty)}，失败 {len(failed)}")
            if index % FLUSH_EVERY == 0:
                merged = save(rows)
                logger.info(f"已落盘 {len(merged)} 行（累计 {merged['日期'].nunique()} 个交易日）")
                rows = []

    merged = save(rows)
    logger.info(
        f"完成：本次成功 {len(days) - len(empty) - len(failed)} 天，"
        f"空 {len(empty)} 天，失败 {len(failed)} 天 | "
        f"文件 {len(merged)} 行 / {merged['日期'].nunique()} 个交易日 / "
        f"{merged['行业编码'].nunique()} 个行业"
    )
    if failed:
        logger.warning(f"失败日期示例: {failed[:10]}")
    return merged


if __name__ == "__main__":
    from utils.set_log import set_log

    set_log("industry_pe_cninfo.log")
    build(latest_only="--latest" in sys.argv)
