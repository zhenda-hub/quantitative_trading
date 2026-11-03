"""行业板块历史 K 线抓取

数据源：ak.stock_board_industry_hist_em(symbol=板块名, period="日k")
- 一次返回一个板块的日线（日期/开/收/高/低/涨跌幅/成交量/成交额/振幅/换手率）
- 实测 0.7 秒/个，496 个行业 4 并发约 1.5 分钟

输出：datas/raw/n_indexes/industry_hist/{板块代码}_{板块名称}.csv
     增量更新：已有文件只补最近 10 天，再按日期去重合并

用法：
    python -m utils.industry_hist            # 增量（新行业回补 2 年）
    python -m utils.industry_hist --full     # 全量重抓（2 年）
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

OUT_DIR = Path("datas/raw/n_indexes/industry_hist")

WORKERS = 2          # 并发过高会被东财限流（返回空表）
CALL_TIMEOUT = 40
RETRY = 3
PACE = 0.12          # 每次请求后的间隔（秒）

# 实测：start_date/end_date 传空字符串会直接返回全历史（约 2590 行，0.13 秒），
# 比指定区间更稳（指定区间时偶发返回空表）
FULL_RANGE = ("", "")

# 只保留最近 N 行（约 3 年），动量只要 120 日、且避免仓库体积膨胀（全历史 159MB）
KEEP_ROWS = 800


def _call_with_timeout(fn, timeout: int = CALL_TIMEOUT):
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


def fetch_industry(name: str, start: str = "", end: str = "") -> pd.DataFrame | None:
    """抓单个板块的日线（传空日期 = 全历史）"""
    import time

    for attempt in range(1, RETRY + 1):
        df, error = _call_with_timeout(
            lambda: ak.stock_board_industry_hist_em(
                symbol=name, start_date=start, end_date=end, period="日k", adjust=""
            )
        )
        if df is not None and len(df):
            time.sleep(PACE)
            return df
        # 空表多数是限流，退避后重试
        time.sleep(1.0 * attempt)
        logger.debug(f"[{name}] 第 {attempt}/{RETRY} 次为空: {error or '空数据'}")
    logger.warning(f"[{name}] 抓取失败（{RETRY} 次均空）")
    return None


def save_one(code: str, name: str, new_df: pd.DataFrame) -> int:
    """与已有文件合并去重后落盘，返回总行数"""
    safe_name = name.replace("/", "").replace("\\", "")
    path = OUT_DIR / f"{code}_{safe_name}.csv"
    if path.exists():
        old = pd.read_csv(path)
        merged = pd.concat([old, new_df], ignore_index=True)
    else:
        merged = new_df

    merged["日期"] = pd.to_datetime(merged["日期"], errors="coerce")
    merged = merged.dropna(subset=["日期"])
    merged = merged.drop_duplicates(subset=["日期"], keep="last")
    merged = merged.sort_values("日期")
    if len(merged) > KEEP_ROWS:
        merged = merged.tail(KEEP_ROWS)
    merged["日期"] = merged["日期"].dt.strftime("%Y-%m-%d")
    merged.to_csv(path, index=False, encoding="utf-8-sig")
    return len(merged)


def build(full: bool = False):
    industries = ak.stock_board_industry_name_em()
    pairs = list(zip(industries["板块代码"].astype(str), industries["板块名称"].astype(str)))
    logger.info(f"行业 {len(pairs)} 个，并发 {WORKERS}，全量={full}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tasks = [(code, name) for code, name in pairs]

    ok, failed = 0, []
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {
            pool.submit(fetch_industry, name): (code, name) for code, name in tasks
        }
        for index, future in enumerate(as_completed(futures), start=1):
            code, name = futures[future]
            try:
                df = future.result()
            except Exception as error:  # noqa: BLE001
                failed.append(name)
                logger.warning(f"[{name}] 异常: {error}")
                continue
            if df is None:
                failed.append(name)
                continue
            save_one(code, name, df)
            ok += 1
            if index % 100 == 0:
                logger.info(f"进度 {index}/{len(tasks)}，成功 {ok}，失败 {len(failed)}")

    files = list(OUT_DIR.glob("*.csv"))
    total_rows = 0
    for path in files:
        total_rows += sum(1 for _ in path.open(encoding="utf-8-sig")) - 1

    logger.info(
        f"完成：成功 {ok}/{len(tasks)}，失败 {len(failed)} | "
        f"文件 {len(files)} 个 / 合计 {total_rows} 行"
    )
    if failed:
        logger.warning(f"失败示例: {failed[:10]}")
    return OUT_DIR


if __name__ == "__main__":
    from utils.set_log import set_log

    set_log("industry_hist.log")
    build(full="--full" in sys.argv)
