"""第一梯队：能源直接冲击 详情页"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import TIER_GROUPS, AKSHARE_SYMBOLS, YFINANCE_SYMBOLS
from data.akshare_client import get_daily_kline, get_minute_kline
from data.yfinance_client import get_daily_data, get_hourly_data
from components.metrics import render_price_card
from components.charts import create_candlestick, create_volume_bar
from components.tables import render_detail_table

st.set_page_config(page_title="能源直接冲击", page_icon="🛢️", layout="wide")
st.title("第一梯队：能源直接冲击")
st.caption("原油、燃料油、LPG、天然气 — 中东冲突直接影响品种")

group = TIER_GROUPS["T1"]
all_symbols = [(s, "akshare") for s in group["akshare"]] + \
              [(s, "yfinance") for s in group["yfinance"]]

symbol_names = []
for sym, src in all_symbols:
    cfg = AKSHARE_SYMBOLS.get(sym) or YFINANCE_SYMBOLS.get(sym, {})
    symbol_names.append(cfg.get("name", sym))

tabs = st.tabs(symbol_names)

for idx, (sym, src) in enumerate(all_symbols):
    cfg = AKSHARE_SYMBOLS.get(sym) or YFINANCE_SYMBOLS.get(sym, {})
    name = cfg.get("name", sym)

    with tabs[idx]:
        # 控制栏：时间粒度 + 技术指标开关
        opt_col1, _, opt_col2 = st.columns([3, 4, 2])
        with opt_col1:
            timeframe = st.radio("时间粒度", ["日线", "小时线"], horizontal=True,
                                key=f"tf_{sym}")
        with opt_col2:
            show_ta = st.checkbox("显示技术指标", key=f"ta_{sym}")

        if src == "akshare":
            if timeframe == "日线":
                df = get_daily_kline(sym)
                date_col = "date"
            else:
                df = get_minute_kline(sym, "60")
                date_col = "datetime"
        else:
            if timeframe == "日线":
                df = get_daily_data(sym)
                date_col = "date"
            else:
                df = get_hourly_data(sym)
                if df is not None and not df.empty and "datetime" in df.columns:
                    date_col = "datetime"
                else:
                    date_col = "date"

        st.divider()

        # 价格指标卡 + K线图
        col_price, col_chart = st.columns([1, 5])
        with col_price:
            render_price_card(name, df)
        with col_chart:
            fig = create_candlestick(df, title=f"{name} K线图",
                                     date_col=date_col,
                                     show_indicators=show_ta)
            st.plotly_chart(fig, use_container_width=True)

        # 成交量（全宽）
        fig = create_volume_bar(df, date_col=date_col)
        st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # 逐日明细（可折叠）
        with st.expander("逐日涨跌明细", expanded=False):
            render_detail_table(df, date_col=date_col)
