"""宏观指标页 — PPI/CPI/PMI（并行加载）"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from data.macro_client import get_ppi, get_cpi, get_pmi
from components.charts import create_line_chart

st.title("宏观指标")
st.caption("PPI / CPI / PMI — 工业通胀与经济景气度核心指标")

# --- 并行加载三个宏观指标（带超时保护） ---
_LOAD_TIMEOUT = 20

with st.spinner("正在加载宏观数据（首次加载可能稍慢）..."):
    with ThreadPoolExecutor(max_workers=3) as executor:
        fut_ppi = executor.submit(get_ppi)
        fut_cpi = executor.submit(get_cpi)
        fut_pmi = executor.submit(get_pmi)

        results = {}
        for name, fut in [("ppi", fut_ppi), ("cpi", fut_cpi), ("pmi", fut_pmi)]:
            try:
                results[name] = fut.result(timeout=_LOAD_TIMEOUT)
            except TimeoutError:
                st.warning(f"{name.upper()} 数据加载超时，请稍后刷新重试")
                results[name] = pd.DataFrame()
            except Exception:
                results[name] = pd.DataFrame()

    ppi_df = results["ppi"]
    cpi_df = results["cpi"]
    pmi_df = results["pmi"]

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
    date_str = latest_date.strftime('%Y-%m-%d') if hasattr(latest_date, 'strftime') else str(latest_date)

    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        st.metric(f"最新 {label}", f"{latest_val}")
    with col2:
        if show_threshold is not None:
            if float(latest_val) >= show_threshold:
                st.success("扩张区间")
            else:
                st.error("收缩区间")
        st.caption(f"数据期: {date_str}")

    st.divider()

    fig = create_line_chart(recent, "date", "value",
                            title=f"{label} 近 24 期趋势", color=color)
    if show_threshold is not None:
        fig.add_hline(y=show_threshold, line_dash="dash", line_color="white",
                      annotation_text=f"荣枯线 {show_threshold}")
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("查看历史数据", expanded=False):
        display = recent[["date", "value"]].copy()
        display["date"] = display["date"].dt.strftime("%Y-%m-%d")
        display = display.iloc[::-1].rename(columns={"date": "日期", "value": "数值"})
        st.dataframe(display, use_container_width=True, hide_index=True)

    # 数据导出
    csv = recent[["date", "value"]].to_csv(index=False).encode("utf-8-sig")
    st.download_button(f"导出 {label} 数据 (CSV)", csv,
                       file_name=f"{label}.csv", mime="text/csv",
                       key=f"export_{label}")


with tab_ppi:
    _render_macro_tab(ppi_df, "PPI", "#FF6B6B")

with tab_cpi:
    _render_macro_tab(cpi_df, "CPI", "#4ECDC4")

with tab_pmi:
    _render_macro_tab(pmi_df, "PMI", "#FFE66D", show_threshold=50)
