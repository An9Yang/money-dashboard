"""Plotly 图表构建器（K线、热力图、迷你图等）"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np


def _calc_ma(series: pd.Series, window: int) -> pd.Series:
    """计算移动平均线"""
    return series.rolling(window=window, min_periods=1).mean()


def _calc_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """计算 RSI 指标"""
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period, min_periods=1).mean()
    avg_loss = loss.rolling(window=period, min_periods=1).mean()
    rsi = pd.Series(50.0, index=series.index)
    valid = (avg_gain + avg_loss) > 0
    rsi[valid] = 100 * avg_gain[valid] / (avg_gain[valid] + avg_loss[valid])
    return rsi


def create_candlestick(df: pd.DataFrame, title: str = "",
                       date_col: str = "date",
                       show_indicators: bool = False) -> go.Figure:
    """创建 K 线图，可选叠加技术指标（MA20/MA60 + RSI）"""
    if df is None or df.empty:
        fig = go.Figure()
        fig.add_annotation(text="暂无数据", x=0.5, y=0.5,
                          xref="paper", yref="paper", showarrow=False,
                          font=dict(size=20, color="gray"))
        return fig

    # 防御性类型转换：确保 OHLC 列为数值类型
    for col in ["open", "high", "low", "close"]:
        if col in df.columns and not pd.api.types.is_numeric_dtype(df[col]):
            df = df.copy()
            df[col] = pd.to_numeric(df[col], errors="coerce")

    x_data = df[date_col] if date_col in df.columns else df.index

    if not show_indicators:
        # 无技术指标：单图模式
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=x_data,
            open=df["open"], high=df["high"],
            low=df["low"], close=df["close"],
            name="K线",
            increasing_line_color="#FF4B4B",
            decreasing_line_color="#00C853",
            increasing_fillcolor="#FF4B4B",
            decreasing_fillcolor="#00C853",
        ))
        fig.update_layout(
            title=title, xaxis_title="日期", yaxis_title="价格",
            template="plotly_dark", height=450,
            xaxis_rangeslider_visible=False,
            margin=dict(l=50, r=20, t=50, b=30),
        )
        return fig

    # 带技术指标：K线 + MA + RSI 子图
    from plotly.subplots import make_subplots
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.7, 0.3],
        subplot_titles=[title, "RSI(14)"],
    )

    # K线
    fig.add_trace(go.Candlestick(
        x=x_data,
        open=df["open"], high=df["high"],
        low=df["low"], close=df["close"],
        name="K线",
        increasing_line_color="#FF4B4B",
        decreasing_line_color="#00C853",
        increasing_fillcolor="#FF4B4B",
        decreasing_fillcolor="#00C853",
    ), row=1, col=1)

    # MA20
    ma20 = _calc_ma(df["close"], 20)
    fig.add_trace(go.Scatter(
        x=x_data, y=ma20, mode="lines",
        line=dict(color="#FFA500", width=1.2),
        name="MA20",
    ), row=1, col=1)

    # MA60
    ma60 = _calc_ma(df["close"], 60)
    fig.add_trace(go.Scatter(
        x=x_data, y=ma60, mode="lines",
        line=dict(color="#4B9DFF", width=1.2),
        name="MA60",
    ), row=1, col=1)

    # RSI
    rsi = _calc_rsi(df["close"], 14)
    fig.add_trace(go.Scatter(
        x=x_data, y=rsi, mode="lines",
        line=dict(color="#E040FB", width=1.2),
        name="RSI(14)",
    ), row=2, col=1)

    # RSI 超买超卖线
    fig.add_hline(y=70, line_dash="dash", line_color="rgba(255,75,75,0.5)",
                  row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="rgba(0,200,83,0.5)",
                  row=2, col=1)

    fig.update_layout(
        template="plotly_dark", height=600,
        xaxis2_rangeslider_visible=False,
        xaxis_rangeslider_visible=False,
        margin=dict(l=50, r=20, t=50, b=30),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_yaxes(title_text="价格", row=1, col=1)
    fig.update_yaxes(title_text="RSI", row=2, col=1, range=[0, 100])

    return fig


def create_volume_bar(df: pd.DataFrame, date_col: str = "date") -> go.Figure:
    """创建成交量柱状图"""
    if df is None or df.empty:
        return go.Figure()

    vol_col = "volume" if "volume" in df.columns else "hold"
    if vol_col not in df.columns:
        return go.Figure()

    # 防御性类型转换
    if not pd.api.types.is_numeric_dtype(df["close"]):
        df = df.copy()
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
    if not pd.api.types.is_numeric_dtype(df[vol_col]):
        df = df.copy()
        df[vol_col] = pd.to_numeric(df[vol_col], errors="coerce")

    colors = []
    for i in range(len(df)):
        if i == 0:
            colors.append("#888888")
        elif df["close"].iloc[i] >= df["close"].iloc[i - 1]:
            colors.append("#FF4B4B")
        else:
            colors.append("#00C853")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df[date_col] if date_col in df.columns else df.index,
        y=df[vol_col],
        marker_color=colors,
        name="成交量",
    ))
    fig.update_layout(
        title="成交量",
        template="plotly_dark",
        height=180,
        margin=dict(l=50, r=20, t=30, b=20),
        xaxis_title="",
        yaxis_title="",
        xaxis_rangeslider_visible=False,
    )
    return fig


def create_heatmap(df: pd.DataFrame) -> go.Figure:
    """创建涨跌幅热力图"""
    if df is None or df.empty:
        return go.Figure()

    categories = df["品种"].tolist()
    z_data = []
    text_data = []
    periods = ["4日涨跌%", "半月涨跌%"]

    for period in periods:
        row = df[period].tolist()
        z_data.append(row)
        text_data.append([f"{v:.2f}%" if pd.notna(v) else "N/A" for v in row])

    fig = go.Figure(data=go.Heatmap(
        z=z_data,
        x=categories,
        y=["4日涨跌%", "半月涨跌%"],
        text=text_data,
        texttemplate="%{text}",
        textfont={"size": 12},
        colorscale=[
            [0, "#00C853"],
            [0.5, "#333333"],
            [1, "#FF4B4B"],
        ],
        zmid=0,
        colorbar=dict(title="涨跌%"),
    ))

    fig.update_layout(
        title="全品种涨跌幅热力图",
        template="plotly_dark",
        height=250,
        margin=dict(l=80, r=20, t=50, b=50),
        xaxis=dict(tickangle=-45),
    )
    return fig


def create_sparkline(data: list, color: str = "#4B9DFF") -> go.Figure:
    """创建迷你走势图"""
    if not data:
        return go.Figure()

    if len(data) >= 2:
        color = "#FF4B4B" if data[-1] >= data[0] else "#00C853"

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        y=data,
        mode="lines",
        line=dict(color=color, width=1.5),
        fill="tozeroy",
        fillcolor=f"rgba({','.join(str(int(color.lstrip('#')[i:i+2], 16)) for i in (0,2,4))}, 0.1)",
    ))
    fig.update_layout(
        height=40,
        width=120,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    return fig


def create_line_chart(df: pd.DataFrame, x_col: str, y_col: str,
                      title: str = "", color: str = "#4B9DFF") -> go.Figure:
    """创建折线图（用于宏观指标）"""
    if df is None or df.empty:
        fig = go.Figure()
        fig.add_annotation(text="暂无数据", x=0.5, y=0.5,
                          xref="paper", yref="paper", showarrow=False,
                          font=dict(size=20, color="gray"))
        return fig

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df[x_col],
        y=df[y_col],
        mode="lines+markers",
        line=dict(color=color, width=2),
        marker=dict(size=4),
    ))
    fig.update_layout(
        title=title,
        template="plotly_dark",
        height=400,
        margin=dict(l=50, r=20, t=50, b=30),
    )
    return fig
