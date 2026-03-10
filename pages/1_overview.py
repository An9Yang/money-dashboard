"""全品种总览 — 核心页面"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from streamlit_autorefresh import st_autorefresh
from datetime import datetime
from config import (AKSHARE_SYMBOLS, YFINANCE_SYMBOLS, TOP_METRICS,
                    TIER_GROUPS, AUTO_REFRESH_DEFAULT_MS, TIERS)
from data.akshare_client import get_daily_kline
from data.yfinance_client import get_daily_data
from data.data_processor import build_overview_row, build_heatmap_data, get_sparkline_data
from components.metrics import render_top_metrics
from components.tables import render_overview_table
from components.charts import create_heatmap, create_sparkline

st.set_page_config(page_title="大宗商品期货监控", page_icon="📊", layout="wide")

# --- 侧边栏 ---
with st.sidebar:
    st.header("刷新设置")
    auto_refresh = st.toggle("自动刷新", value=True)
    refresh_interval = st.select_slider(
        "刷新间隔",
        options=[60, 120, 300, 600],
        value=300,
        format_func=lambda x: f"{x // 60} 分钟",
    )
    if auto_refresh:
        st_autorefresh(interval=refresh_interval * 1000, key="overview_refresh")
    st.divider()
    st.caption(f"最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# --- 标题 ---
st.title("大宗商品期货监控")
st.caption("中东局势升级 — 原油及石化产业链品种实时追踪")

# --- 加载数据 ---
with st.spinner("正在加载数据..."):
    # 顶部指标品种数据
    top_data = {}
    top_config = {}
    for sym in TOP_METRICS:
        if sym in YFINANCE_SYMBOLS:
            top_data[sym] = get_daily_data(sym)
            top_config[sym] = YFINANCE_SYMBOLS[sym]
        elif sym in AKSHARE_SYMBOLS:
            top_data[sym] = get_daily_kline(sym)
            top_config[sym] = AKSHARE_SYMBOLS[sym]

    # 全品种数据
    all_data = {}
    for sym, cfg in AKSHARE_SYMBOLS.items():
        all_data[sym] = get_daily_kline(sym)
    for sym, cfg in YFINANCE_SYMBOLS.items():
        all_data[sym] = get_daily_data(sym)

# --- 顶部指标卡 ---
render_top_metrics(top_data, top_config)

st.divider()

# --- 全品种汇总表 ---
st.subheader("全品种涨跌一览")

overview_rows = []
for tier_id in ["T1", "T2", "T3"]:
    group = TIER_GROUPS[tier_id]
    for sym in group["akshare"]:
        cfg = AKSHARE_SYMBOLS[sym]
        row = build_overview_row(sym, cfg["name"], tier_id, cfg["exchange"],
                                 all_data.get(sym))
        overview_rows.append(row)
    for sym in group["yfinance"]:
        cfg = YFINANCE_SYMBOLS[sym]
        row = build_overview_row(sym, cfg["name"], tier_id, cfg["exchange"],
                                 all_data.get(sym))
        overview_rows.append(row)

render_overview_table(overview_rows)

st.divider()

# --- 迷你走势图 ---
st.subheader("近两周走势一览")
sparkline_cols = st.columns(5)
for i, row in enumerate(overview_rows):
    sym = row["代码"]
    df = all_data.get(sym)
    spark_data = get_sparkline_data(df, 15)
    if spark_data:
        col_idx = i % 5
        with sparkline_cols[col_idx]:
            fig = create_sparkline(spark_data)
            st.plotly_chart(fig, width="stretch", key=f"spark_{sym}")
            st.caption(row["品种"])

st.divider()

# --- 热力图 ---
st.subheader("涨跌幅热力图")
heatmap_df = build_heatmap_data(overview_rows)
if not heatmap_df.empty:
    fig = create_heatmap(heatmap_df)
    st.plotly_chart(fig, width="stretch")
else:
    st.info("数据不足，无法生成热力图")
