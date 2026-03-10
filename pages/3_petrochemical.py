"""第二梯队：石化产业链传导 详情页"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import TIER_GROUPS, AKSHARE_SYMBOLS
from data.akshare_client import get_daily_kline, get_minute_kline
from components.metrics import render_price_card
from components.charts import create_candlestick, create_volume_bar
from components.tables import render_detail_table

st.set_page_config(page_title="石化产业链传导", page_icon="🏭", layout="wide")
st.title("第二梯队：石化产业链传导")
st.caption("甲醇、PTA、乙二醇、PP、LLDPE 等 — 原油成本传导品种")

group = TIER_GROUPS["T2"]
symbols = group["akshare"]

symbol_names = [AKSHARE_SYMBOLS[s]["name"] for s in symbols]
tabs = st.tabs(symbol_names)

for idx, sym in enumerate(symbols):
    cfg = AKSHARE_SYMBOLS[sym]
    name = cfg["name"]

    with tabs[idx]:
        opt_col1, opt_col2 = st.columns([2, 1])
        with opt_col1:
            timeframe = st.radio("时间粒度", ["日线", "小时线"], horizontal=True,
                                key=f"tf_{sym}")
        with opt_col2:
            show_ta = st.checkbox("显示技术指标", key=f"ta_{sym}")

        if timeframe == "日线":
            df = get_daily_kline(sym)
            date_col = "date"
        else:
            df = get_minute_kline(sym, "60")
            date_col = "datetime"

        col1, col2, col3 = st.columns([1, 3, 3])
        with col1:
            render_price_card(name, df)
        with col2:
            fig = create_candlestick(df, title=f"{name} K线图",
                                     date_col=date_col,
                                     show_indicators=show_ta)
            st.plotly_chart(fig, width="stretch")
        with col3:
            fig = create_volume_bar(df, date_col=date_col)
            st.plotly_chart(fig, width="stretch")

        st.subheader("逐日涨跌明细")
        render_detail_table(df, date_col=date_col)
