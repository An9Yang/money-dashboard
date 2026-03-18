"""第三梯队：避险 & 间接影响 详情页"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from datetime import datetime
from config import (TIER_GROUPS, AKSHARE_SYMBOLS, COLOR_SCHEMES, COLORS,
                    TRADING_SESSIONS)
from data.akshare_client import get_daily_kline, get_minute_kline
from components.metrics import render_price_card
from components.charts import create_candlestick, create_volume_bar, create_oi_chart
from components.tables import render_detail_table

st.title("第三梯队：避险 & 间接影响")
st.caption("黄金、白银、20号胶 — 避险资产与间接影响品种")

with st.sidebar:
    scheme_name = st.selectbox("涨跌颜色方案", list(COLOR_SCHEMES.keys()),
                               index=0, key="haven_color")
    st.session_state["color_scheme"] = COLOR_SCHEMES[scheme_name]
    colors = COLOR_SCHEMES[scheme_name]

group = TIER_GROUPS["T3"]
symbols = group["akshare"]

symbol_names = [AKSHARE_SYMBOLS[s]["name"] for s in symbols]
tabs = st.tabs(symbol_names)

for idx, sym in enumerate(symbols):
    cfg = AKSHARE_SYMBOLS[sym]
    name = cfg["name"]
    exchange = cfg.get("exchange", "")

    with tabs[idx]:
        opt_col1, opt_col2, opt_col3 = st.columns([2, 4, 2])
        with opt_col1:
            timeframe = st.radio("时间粒度", ["日线", "小时线"], horizontal=True,
                                 key=f"tf_{sym}")
        with opt_col2:
            indicators = st.multiselect(
                "技术指标",
                ["MA", "BOLL", "RSI", "MACD", "KDJ", "VWAP"],
                default=[], key=f"ta_{sym}",
            )
        with opt_col3:
            session_info = TRADING_SESSIONS.get(exchange, {})
            if "day" in session_info:
                day_s = session_info["day"]
                night_s = session_info.get("night", "")
                session_str = f"日盘 {day_s}"
                if night_s:
                    session_str += f"\n夜盘 {night_s}"
            else:
                session_str = "—"
            st.caption(f"交易时段\n{session_str}")

        if timeframe == "日线":
            df = get_daily_kline(sym)
            date_col = "date"
        else:
            df = get_minute_kline(sym, "60")
            date_col = "datetime"

        st.divider()

        col_price, col_chart = st.columns([1, 5])
        with col_price:
            render_price_card(name, df)
        with col_chart:
            fig = create_candlestick(df, title=f"{name} K线图",
                                     date_col=date_col,
                                     indicators=indicators,
                                     color_up=colors["up"],
                                     color_down=colors["down"])
            st.plotly_chart(fig, use_container_width=True)

        fig = create_volume_bar(df, date_col=date_col,
                                color_up=colors["up"], color_down=colors["down"])
        st.plotly_chart(fig, use_container_width=True)

        # 持仓量
        if df is not None and not df.empty and "hold" in df.columns:
            with st.expander("持仓量 (OI) 分析", expanded=False):
                fig = create_oi_chart(df, date_col=date_col,
                                      color_up=colors["up"],
                                      color_down=colors["down"])
                st.plotly_chart(fig, use_container_width=True)

        st.divider()

        col_detail, col_export = st.columns([4, 1])
        with col_export:
            if df is not None and not df.empty:
                csv = df.to_csv(index=False).encode("utf-8-sig")
                st.download_button(
                    "导出 CSV", csv,
                    file_name=f"{sym}_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv", key=f"export_{sym}",
                )

        with st.expander("逐日涨跌明细", expanded=False):
            render_detail_table(df, date_col=date_col)
