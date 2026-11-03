# quantitative_trading

## pip-tools

```cmd
.venv\Scripts\activate
```


```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.in .
RUN pip install pip-tools \
    && pip-compile requirements.in \
    && pip-sync requirements.txt

COPY . .

CMD ["python", "main.py"]

```



```bash
pip install pip-tools

pip-compile requirements.in
pip-compile --upgrade

# 会删除多余包, 包严格一致
pip-sync requirements.txt


```

## pipdeptree

```bash
pip install pipdeptree
pipdeptree
```



## st
```bash
streamlit run your_app.py

```

TODO:

- [x] bond
  - [x] 数据
  - [x] 绘图
  - [x] 策略(指标, 买卖)
  - [x] 国债
- [x] reits
  - [x] 数据
  - [x] 绘图
  - [ ] 策略(指标, 买卖)
- [x] gold
  - [x] 数据
  - [x] 绘图
  - [ ] 策略(指标, 买卖)
- [x] news
  - [x] 数据
  - [x] 绘图
- [x] index
  - [x] 数据
  - [x] 绘图
  - [ ] 策略(指标, 买卖)
- [x] virtual
  - [x] 数据
  - [x] 绘图
  - [ ] 策略(指标, 买卖)

行业

- [x] 行业板块页
  - [x] 数据：`datas/raw/stocks/ef_行业板块.csv`（496 行业快照，PE/换手/量比/成交额）
  - [x] 绘图：Treemap（面积=总市值，红涨绿跌）+ 气泡图 + 横向条形图
  - [x] 行业估值自算：`utils/industry_valuation.py`（PE/PB 中位数 + 流通市值加权，按日追加）
  - [x] 行业↔ETF 映射：`etf_industry_map.csv` / `industry_etf_map.csv`（196/496 行业有对应 ETF）
  - [ ] 策略(指标, 买卖)

- [ ] **行业估值分位**（进行中）
  - [x] PE 历史回填：巨潮国证行业市盈率，829 个交易日 / 293 行业 / 24.3 万行
        输出 `datas/processed/n_indexes/industry_pe_cninfo.csv`，2023-06 起
        脚本 `utils/industry_valuation_cninfo.py`（`--latest` 只抓最新一天）
  - [ ] **PB 历史回填**（待做）
        源：`stock_value_em(symbol)` 个股 PE/PB 历史（2018-01 起，2142 行/只）
        路径：逐只抓取 → 每月末采样 → 按行业成分股流通市值加权 → 行业 PB 月频历史
        成本：5563 只 × 0.99s，4 并发约 23 分钟，存储约 60MB（月采样 96 期，日频 11.7M 行太重）
        坑：幸存者偏差（用当前成分股回溯）；申万周报接口已失效、巨潮只给 PE
  - [ ] 分位计算
        PE 分位：近 3 年 829 期，bootstrap SD ≈ 4%（已实测：<36 期不可用，≥60 期可用）
        周期行业 PE 分位失效 → 切 PB 分位：煤炭/钢铁/有色/化工/航运/养殖/水泥/玻璃
        温度 = PE分位×50% + PB分位×50%；分档 <20% 偏冷 / 20-80% 中性 / >80% 偏热
  - [ ] 页面：行业估值分位榜（PE/PB 分位 + 温度 + 对应 ETF）

- [ ] 行业动量/轮动榜
  - [ ] 行业历史 K 线抓取（`stock_board_industry_hist_em`，496 个 × 0.7s ≈ 6 分钟）
  - [ ] 20/60/120 日动量 + 相对强弱 RS + 拥挤度（换手/成交额占比）
  - [ ] 景气度：`stock_yjbb_em` 业绩报表（净利润同比/ROE/毛利率，含所处行业字段）

交易
回测

已知问题

- [ ] 集思录 cookie 失效（`.env` 的 `JISILU_COOKIES`）→ `bond_cb_jsl` 只返回 30 行
- [ ] REITs 部分标的解析失败（`reits_hist_em` Length mismatch，约 10 只，不影响合并）
- [ ] `requirements.in` / `requirements.txt` 已被 uv 取代，但 Dockerfile 仍在用 → 要么改 Dockerfile 要么保留文件



TA-Lib: 提供 200+ 技术指标（如 SMA、RSI、MACD）。
pandas_ta: 轻量、易用，集成 Pandas。



性能优化:

- [x] metals: 计算单价
- [x] reits, index: 多个csv读取,很慢, 改用保存结果
- [x] Linear Scale 和 Log Scale：已实现视图模式切换功能

## 图表视图模式配置

| 页面 | 图表 | 视图模式支持 | 默认模式 | 数据类型 |
|------|------|------------|---------|---------|
| virtual | 加密货币价格走势 | 归一化/对数/线性 ✅ | 归一化 | 价格(USD) |
| metals | 贵金属价格走势 | 归一化/对数/线性 ✅ | 对数 | 价格(USD/盎司) |
| reits | REITs价格走势 | 归一化/对数/线性 ✅ | 对数 | 开盘价 |
| company | 股票K线图 | 对数/线性 ✅ | 对数 | 价格 |
| index | 全球指数走势 | 归一化/对数/线性 ✅ | 归一化 | 指数点数 |
| industry | 行业板块气泡图 | 无（固定对数） | - | 涨跌幅%,市值 |
| bond | 国债收益率曲线 | 无（固定线性） | - | 收益率(%) |
| period | GDP/CPI散点图 | 无（固定线性） | - | 百分比 |
| allocation | 资产配置饼图 | 无（饼图不适用） | - | 比例 |

### 视图模式说明
- **归一化**：所有资产起点为1，直接比较收益率
- **对数**：相同百分比变化显示为相同垂直距离，适合长期趋势
- **线性**：显示原始绝对价格




- [ ] 按钮刷新数据的日志问题
- [ ] 统一异常处理
$市值 = 单价 \times 流通供应量$