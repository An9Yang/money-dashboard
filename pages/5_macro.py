"""宏观指标页 — PPI/CPI/PMI"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.macro_client import get_ppi, get_cpi, get_pmi
from components.charts import create_line_chart

st.set_page_config(page_title="宏观指标", page_icon="📈", layout="wide")
st.title("宏观指标")
st.caption("PPI / CPI / PMI — 工业通胀与经济景气度核心指标")

tab_ppi, tab_cpi, tab_pmi = st.tabs(["PPI 生产者物价指数", "CPI 居民消费价格指数", "PMI 采购经理指数"])


def _render_macro_tab(df, label, color, show_threshold=None):
    """通用宏观指标渲染"""
    if df.empty or "value" not in df.columns:
        st.info(f"{label} 数据暂时不可用")
        return

    recent = df.dropna(subset=["value"]).tail(24)
    if recent.empty:
        st.info(f"{label} 无有效数据")
        return

    latest_val = recent["value"].iloc[-1]
    latest_date = recent["date"].iloc[-1]

    col1, col2 = st.columns([1, 3])
    with col1:
        st.metric(f"最新 {label}", f"{latest_val}")
        if show_threshold is not None:
            if float(latest_val) >= show_threshold:
                st.success("扩张区间")
            else:
                st.error("收缩区间")
    with col2:
        st.caption(f"数据期: {latest_date.strftime('%Y-%m-%d') if hasattr(latest_date, 'strftime') else latest_date}")

    fig = create_line_chart(recent, "date", "value",
                            title=f"{label} 近 24 期趋势", color=color)
    if show_threshold is not None:
        fig.add_hline(y=show_threshold, line_dash="dash", line_color="white",
                     annotation_text=f"荣枯线 {show_threshold}")
    st.plotly_chart(fig, width="stretch")

    # 展示表格
    display = recent[["date", "value"]].copy()
    display["date"] = display["date"].dt.strftime("%Y-%m-%d")
    display = display.iloc[::-1].rename(columns={"date": "日期", "value": "数值"})
    st.dataframe(display, width="stretch", hide_index=True)


with tab_ppi:
    with st.spinner("加载 PPI 数据..."):
        ppi_df = get_ppi()
    _render_macro_tab(ppi_df, "PPI", "#FF6B6B")

with tab_cpi:
    with st.spinner("加载 CPI 数据..."):
        cpi_df = get_cpi()
    _render_macro_tab(cpi_df, "CPI", "#4ECDC4")

with tab_pmi:
    with st.spinner("加载 PMI 数据..."):
        pmi_df = get_pmi()
    _render_macro_tab(pmi_df, "PMI", "#FFE66D", show_threshold=50)
