"""行业 ↔ ETF 映射

数据来源：
- 行业清单：ak.stock_board_industry_name_em()（496 个行业，含板块代码）
- ETF 行情：ak.fund_etf_spot_em()（约 1664 只，含成交额/份额/折价率/主力净流入）

设计：以「ETF → 行业/分类」为主表（全覆盖），再从中派生「行业 → Top5 ETF」，
      避免两套匹配规则各自跑、结果对不上（曾出现最大 ETF 被漏掉的问题）。

输出（只保留两个文件）：
- datas/reference/etf_industry_map.csv    主表：ETF → 分类/匹配行业（1664 行，按成交额倒序）
- datas/reference/industry_etf_map.csv    派生：行业 → Top5 ETF（按成交额倒序，不做人工维护）

匹配口径：
- ETF 主题词 = 名称里 "ETF" 之前的部分（「光伏ETF富国」→「光伏」）
- 行业名归一化去掉 Ⅱ/Ⅲ 等罗马数字后缀
- 匹配强度 exact > prefix > contains，但**排序只看成交额**（流动性优先）
- 行业与 ETF 习惯叫法不一致的，走 ALIAS / TOKEN_ALIAS 映射
"""
from __future__ import annotations

import re
from pathlib import Path

import akshare as ak
import pandas as pd
from loguru import logger

REVERSE = Path("datas/reference/etf_industry_map.csv")
FORWARD = Path("datas/reference/industry_etf_map.csv")
OBSOLETE = [
    Path("datas/reference/industry_etf_candidates.csv"),   # 旧版候选表（排序有偏差）
]

MAX_PER_INDUSTRY = 5      # 每个行业最多保留几只 ETF
ROMAN_SUFFIX = re.compile(r"(Ⅱ|Ⅲ|Ⅱ|III|II|IV|Ⅰ)$")
ETF_NOISE = re.compile(r"(ETF|etf|指数|基金|联接|LOF|场内)")

# 行业名 → ETF 主题词的同义词（名称对不上但实际同一个赛道的，显式声明）
ALIAS = {
    "白酒": ["酒"],
    "非白酒": ["酒"],
    "其他酒类": ["酒"],
    "军工电子": ["军工", "国防"],
    "国防军工": ["军工", "国防"],
    "电池": ["锂电池", "新能源车"],
    "光伏设备": ["光伏"],
    "通信设备": ["通信"],
    "软件开发": ["软件"],
    "证券": ["券商"],
}

# ETF 主题词 → 东财行业（行业词与 ETF 习惯叫法不一致的）
TOKEN_ALIAS = {
    "芯片": "半导体",
    "算力": "IT服务",
    "人工智能": "软件开发",
    "金融科技": "软件开发",
    "创新药": "化学制药",
    "疫苗": "生物制品",
    "固态电池": "电池",
    "储能": "电池",
    "低空经济": "航空装备",
    "机器人": "自动化设备",
    "军工": "国防军工",
    "酒": "白酒",
}

# 非行业类 ETF 的归类关键词（按优先级从上到下）
CATEGORY_KEYWORDS = [
    ("货币", ["日利", "添益", "货币", "现金", "保证金"]),
    ("宽基", ["沪深300", "中证500", "中证1000", "中证2000", "A500", "上证50", "上证180",
              "上证指数", "上证", "创业板", "科创50", "科创100", "科创200", "科创创业",
              "科创", "深证100", "深证", "中证", "国证", "MSCI", "基本面", "A股",
              "综指", "全指", "双创", "中证A", "北证"]),
    ("跨境", ["港股", "香港", "恒生", "恒科", "纳指", "纳斯达克", "标普", "道琼斯", "德国",
              "日经", "法国", "东南亚", "印度", "越南", "中概", "海外", "亚太", "美国",
              "沙特", "欧洲", "日本", "中韩"]),
    ("商品", ["黄金", "白银", "原油", "豆粕", "能源化工", "商品"]),
    ("策略", ["红利", "低波", "价值", "成长", "质量", "动量", "等权", "自由现金流",
              "国企改革", "央企", "国企"]),
]

RANK_LABEL = {0: "exact", 1: "prefix", 2: "contains"}


def normalize(text: str) -> str:
    """行业名/ETF 名归一化：ETF 取 "ETF" 之前的部分，行业名去掉罗马数字后缀"""
    out = str(text).strip()
    if "ETF" in out:
        out = out.split("ETF")[0]
    elif "etf" in out:
        out = out.split("etf")[0]
    out = ROMAN_SUFFIX.sub("", out)
    out = ETF_NOISE.sub("", out)
    return out.replace(" ", "").replace("　", "")


def match_rank(token: str, keyword: str):
    """匹配强度：0=exact 1=prefix 2=contains None=不匹配"""
    if not token or not keyword:
        return None
    if token == keyword:
        return 0
    if token.startswith(keyword) or keyword.startswith(token):
        return 1
    if len(token) >= 2 and len(keyword) >= 2 and (keyword in token or token in keyword):
        return 2
    return None


def classify_token(token: str) -> str:
    """给未匹配到行业的 ETF 归类"""
    for category, keywords in CATEGORY_KEYWORDS:
        if any(k in token for k in keywords):
            return category
    return "其他"


def load_industries() -> pd.DataFrame:
    df = ak.stock_board_industry_name_em()
    df = df[["板块名称", "板块代码"]].copy()
    df["归一化"] = df["板块名称"].map(normalize)
    return df


def load_etfs() -> pd.DataFrame:
    raw = ak.fund_etf_spot_em()
    keep = {
        "代码": "ETF代码",
        "名称": "ETF名称",
        "成交额": "成交额",
        "最新份额": "最新份额",
        "基金折价率": "折价率",
        "主力净流入-净额": "主力净流入",
    }
    df = raw[[c for c in keep if c in raw.columns]].rename(columns=keep)
    for column in ("成交额", "最新份额", "折价率", "主力净流入"):
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")
    df["归一化"] = df["ETF名称"].map(normalize)
    df = df.dropna(subset=["成交额"]).copy()
    df["成交额(亿)"] = (df["成交额"] / 1e8).round(2)
    df["最新份额(亿份)"] = (df["最新份额"] / 1e8).round(2) if "最新份额" in df else None
    df["主力净流入(亿)"] = (df["主力净流入"] / 1e8).round(2) if "主力净流入" in df else None
    return df


def build_reverse(industries: pd.DataFrame, etfs: pd.DataFrame):
    """构造 ETF → 行业/分类，同时返回 行业 → ETF 的索引供派生用"""
    # 行业关键词 -> 行业名
    pairs = []
    for _, ind in industries.iterrows():
        norm = ind["归一化"]
        for keyword in [k for k in [norm, *ALIAS.get(norm, [])] if k]:
            pairs.append((keyword, ind["板块名称"]))

    records, industry_index = [], {}
    for _, etf in etfs.iterrows():
        token = etf["归一化"]
        hits = []
        for keyword, industry_name in pairs:
            rank = match_rank(token, keyword)
            if rank is not None:
                hits.append((rank, industry_name))

        if hits:
            hits.sort(key=lambda x: x[0])
            matched = list(dict.fromkeys(name for _, name in hits))
            best_rank = {name: min(r for r, n in hits if n == name) for name in matched}
            category = "行业"
        else:
            alias_hit = [v for k, v in TOKEN_ALIAS.items() if k in token]
            if alias_hit:
                matched = list(dict.fromkeys(alias_hit))
                best_rank = {name: 2 for name in matched}
                category = "行业"
            else:
                matched, best_rank = [], {}
                category = classify_token(token)

        row = {
            "ETF代码": etf["ETF代码"],
            "ETF名称": etf["ETF名称"],
            "主题词": token,
            "分类": category,
            "匹配行业数": len(matched),
            "匹配行业": "|".join(matched[:3]),
            "成交额(亿)": etf["成交额(亿)"],
            "最新份额(亿份)": etf.get("最新份额(亿份)"),
            "折价率": etf.get("折价率"),
            "主力净流入(亿)": etf.get("主力净流入(亿)"),
        }
        records.append(row)

        for name in matched:
            industry_index.setdefault(name, []).append({
                "ETF代码": row["ETF代码"],
                "ETF名称": row["ETF名称"],
                "ETF主题词": token,
                "匹配方式": RANK_LABEL[best_rank[name]],
                "成交额(亿)": row["成交额(亿)"],
                "最新份额(亿份)": row["最新份额(亿份)"],
                "折价率": row["折价率"],
                "主力净流入(亿)": row["主力净流入(亿)"],
            })

    df = pd.DataFrame(records).sort_values("成交额(亿)", ascending=False)
    REVERSE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(REVERSE, index=False, encoding="utf-8-sig")
    logger.info(
        f"{REVERSE} 已生成: {len(df)} 只 ETF，分类 {df['分类'].value_counts().to_dict()}，"
        f"合计成交额 {df['成交额(亿)'].sum():.0f} 亿"
    )
    return df, industry_index


def build_forward(industries: pd.DataFrame, industry_index: dict, output: Path = FORWARD):
    """从反向索引派生 行业 → Top5 ETF（按成交额倒序，流动性优先）"""
    rows = []
    for _, ind in industries.iterrows():
        candidates = sorted(
            industry_index.get(ind["板块名称"], []),
            key=lambda r: -(r["成交额(亿)"] or 0),
        )[:MAX_PER_INDUSTRY]

        if not candidates:
            rows.append({
                "板块代码": ind["板块代码"],
                "板块名称": ind["板块名称"],
                "ETF代码": None,
                "ETF名称": None,
                "ETF主题词": None,
                "匹配方式": None,
                "成交额(亿)": None,
                "最新份额(亿份)": None,
                "折价率": None,
                "主力净流入(亿)": None,
            })
            continue

        for rank, c in enumerate(candidates, start=1):
            rows.append({
                "板块代码": ind["板块代码"],
                "板块名称": ind["板块名称"],
                "排名": rank,
                **c,
            })

    df = pd.DataFrame(rows)
    if "排名" not in df.columns:
        df["排名"] = None
    df.to_csv(output, index=False, encoding="utf-8-sig")

    covered = int(df.dropna(subset=["ETF代码"])["板块名称"].nunique())
    logger.info(
        f"{output} 已生成: {len(df)} 行，覆盖 {covered}/{len(industries)} 个行业"
        f"（每行业最多 {MAX_PER_INDUSTRY} 只，按成交额倒序）"
    )
    return df


def build_map():
    """单一入口：生成反向主表 + 派生正向表，并清理旧版文件"""
    industries = load_industries()
    etfs = load_etfs()
    logger.info(f"行业 {len(industries)} 个 / ETF {len(etfs)} 只（有成交额）")

    _, industry_index = build_reverse(industries, etfs)
    build_forward(industries, industry_index)

    for path in OBSOLETE:
        if path.exists():
            path.unlink()
            logger.info(f"已删除旧文件: {path}")


if __name__ == "__main__":
    from utils.set_log import set_log

    set_log("industry_etf_map.log")
    build_map()
