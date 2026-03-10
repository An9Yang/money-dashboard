"""价格指标卡片"""

import streamlit as st
import pandas as pd
from data.data_processor import get_latest_price


def render_top_metrics(data_dict: dict, symbol_config: dict):
    """渲染顶部 4 个指标卡片"""
    cols = st.columns(len(data_dict))
    for i, (symbol, df) in enumerate(data_dict.items()):
        config = symbol_config.get(symbol, {})
        name = config.get("name", symbol)
        info = get_latest_price(df)

        with cols[i]:
            if info["close"] is not None:
                delta_str = f"{info['change_1d']:+.2f}%" if info["change_1d"] is not None else None
                st.metric(
                    label=name,
                    value=f"{info['close']:,.2f}",
                    delta=delta_str,
                    delta_color="normal",
                )
            else:
                st.metric(label=name, value="N/A", delta=None)


def render_price_card(name: str, df: pd.DataFrame):
    """渲染单品种价格卡片"""
    info = get_latest_price(df)
    if info["close"] is not None:
        delta_str = f"{info['change_1d']:+.2f}%" if info["change_1d"] is not None else None
        st.metric(
            label=name,
            value=f"{info['close']:,.2f}",
            delta=delta_str,
            delta_color="normal",
        )
    else:
        st.metric(label=name, value="N/A", delta=None)
