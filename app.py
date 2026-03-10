"""
大宗商品期货监控 Dashboard
中东局势升级 — 原油及石化产业链品种实时追踪

Streamlit 入口 + 多页导航
"""

import streamlit as st

st.set_page_config(
    page_title="大宗商品期货监控",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("大宗商品期货监控 Dashboard")

st.markdown("""
### 监控体系

本 Dashboard 按**冲突影响层级**追踪期货品种涨跌：

| 梯队 | 类别 | 品种 |
|---|---|---|
| **T1** | 能源直接冲击 | 原油(SC/WTI/Brent)、燃料油、LPG、天然气 |
| **T2** | 石化产业链传导 | 甲醇、PTA、乙二醇、PP、LLDPE、PVC、沥青、苯乙烯 |
| **T3** | 避险 & 间接影响 | 黄金、白银、20号胶 |

### 页面导航

使用左侧菜单切换页面：

- **总览** — 全品种汇总表 + 热力图 + 迷你走势
- **能源直接冲击** — 第一梯队品种 K 线详情
- **石化产业链传导** — 第二梯队品种 K 线详情
- **避险 & 间接影响** — 第三梯队品种 K 线详情
- **宏观指标** — PPI / CPI / PMI 趋势

### 数据源

- **中国期货**: AKShare (上期所/大商所/郑商所/INE)
- **国际期货**: yfinance (NYMEX/ICE)
- **宏观数据**: AKShare 宏观模块
""")

st.divider()
st.caption("点击左侧「总览」页面开始使用 →")
