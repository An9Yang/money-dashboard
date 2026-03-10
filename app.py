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
st.caption("中东局势升级 — 原油及石化产业链品种实时追踪")

st.divider()

# 梯队概览卡片
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("""
    #### T1 能源直接冲击
    原油 (SC / WTI / Brent)、燃料油、LPG、天然气

    受中东局势影响最直接的能源品种
    """)
with col2:
    st.markdown("""
    #### T2 石化产业链传导
    甲醇、PTA、乙二醇、PP、LLDPE、PVC、沥青、苯乙烯

    原油成本端传导的中下游化工品
    """)
with col3:
    st.markdown("""
    #### T3 避险 & 间接影响
    黄金、白银、20号胶

    避险资产与间接受影响品种
    """)

st.divider()

st.markdown("""
#### 页面导航

使用左侧菜单切换页面：

| 页面 | 内容 |
|---|---|
| **总览** | 全品种汇总表 + 热力图 + 迷你走势 + 资讯预览 |
| **能源直接冲击** | 第一梯队品种 K 线详情（可选技术指标） |
| **石化产业链传导** | 第二梯队品种 K 线详情（可选技术指标） |
| **避险 & 间接影响** | 第三梯队品种 K 线详情（可选技术指标） |
| **宏观指标** | PPI / CPI / PMI 趋势 |
| **实时资讯** | 财联社电报（大宗商品关键词过滤） |
""")

st.divider()

st.markdown("""
<small>

**数据源** &nbsp; 中国期货: AKShare (上期所/大商所/郑商所/INE) &nbsp;|&nbsp; 国际期货: yfinance (NYMEX/ICE) &nbsp;|&nbsp; 宏观数据: AKShare &nbsp;|&nbsp; 新闻: 财联社电报

</small>
""", unsafe_allow_html=True)

st.caption("点击左侧「总览」页面开始使用 →")
