"""Plotly 图表构建器（K线、热力图、迷你图、技术指标、对比图等）"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np


# ─── 技术指标计算 ───────────────────────────────────────────

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


def _calc_macd(series: pd.Series, fast: int = 12, slow: int = 26,
               signal: int = 9) -> tuple:
    """计算 MACD 指标，返回 (MACD线, 信号线, 柱状图)"""
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def _calc_bollinger(series: pd.Series, window: int = 20,
                    num_std: int = 2) -> tuple:
    """计算布林带，返回 (上轨, 中轨, 下轨)"""
    ma = series.rolling(window=window, min_periods=1).mean()
    std = series.rolling(window=window, min_periods=1).std().fillna(0)
    upper = ma + num_std * std
    lower = ma - num_std * std
    return upper, ma, lower


def _calc_kdj(df: pd.DataFrame, n: int = 9, m1: int = 3,
              m2: int = 3) -> tuple:
    """计算 KDJ 指标，返回 (K, D, J)"""
    low_n = df["low"].rolling(window=n, min_periods=1).min()
    high_n = df["high"].rolling(window=n, min_periods=1).max()
    denom = high_n - low_n
    rsv = pd.Series(50.0, index=df.index)
    valid = denom > 0
    rsv[valid] = (df["close"][valid] - low_n[valid]) / denom[valid] * 100
    k = rsv.ewm(com=m1 - 1, adjust=False).mean()
    d = k.ewm(com=m2 - 1, adjust=False).mean()
    j = 3 * k - 2 * d
    return k, d, j


def _calc_vwap(df: pd.DataFrame) -> pd.Series:
    """计算成交量加权均价 (VWAP)"""
    if "volume" not in df.columns:
        return pd.Series(dtype=float, index=df.index)
    vol = pd.to_numeric(df["volume"], errors="coerce").fillna(0)
    tp = (df["high"] + df["low"] + df["close"]) / 3
    cumvol = vol.cumsum()
    cumtp = (tp * vol).cumsum()
    vwap = pd.Series(np.nan, index=df.index)
    valid = cumvol > 0
    vwap[valid] = cumtp[valid] / cumvol[valid]
    return vwap


# ─── K线图（支持多种技术指标）───────────────────────────────

def create_candlestick(df: pd.DataFrame, title: str = "",
                       date_col: str = "date",
                       show_indicators: bool = False,
                       indicators: list = None,
                       color_up: str = "#FF4B4B",
                       color_down: str = "#00C853") -> go.Figure:
    """
    创建 K 线图，支持多种技术指标叠加。

    Parameters
    ----------
    indicators : list of str, optional
        技术指标列表，可选: "MA", "BOLL", "RSI", "MACD", "KDJ", "VWAP"
    show_indicators : bool
        旧版兼容参数，True 等价于 indicators=["MA", "RSI"]
    color_up / color_down : str
        涨/跌颜色（支持中国/国际配色方案切换）
    """
    if df is None or df.empty:
        fig = go.Figure()
        fig.add_annotation(text="暂无数据", x=0.5, y=0.5,
                           xref="paper", yref="paper", showarrow=False,
                           font=dict(size=20, color="gray"))
        return fig

    # 旧版兼容：show_indicators=True → ["MA", "RSI"]
    if indicators is None:
        indicators = ["MA", "RSI"] if show_indicators else []

    # 防御性类型转换
    df = df.copy()
    for col in ["open", "high", "low", "close"]:
        if col in df.columns and not pd.api.types.is_numeric_dtype(df[col]):
            df[col] = pd.to_numeric(df[col], errors="coerce")

    x_data = df[date_col] if date_col in df.columns else df.index

    # 确定子图布局：RSI/MACD/KDJ 各需独立面板
    sub_panels = [i for i in indicators if i in ("RSI", "MACD", "KDJ")]
    n_rows = 1 + len(sub_panels)

    if n_rows == 1:
        fig = go.Figure()
    else:
        heights = [0.6] + [round(0.4 / len(sub_panels), 2)] * len(sub_panels)
        sub_titles = [title] + [p for p in sub_panels]
        fig = make_subplots(
            rows=n_rows, cols=1, shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=heights,
            subplot_titles=sub_titles,
        )

    # ── K 线主图 ──
    candle = go.Candlestick(
        x=x_data,
        open=df["open"], high=df["high"],
        low=df["low"], close=df["close"],
        name="K线",
        increasing_line_color=color_up,
        decreasing_line_color=color_down,
        increasing_fillcolor=color_up,
        decreasing_fillcolor=color_down,
    )
    if n_rows == 1:
        fig.add_trace(candle)
    else:
        fig.add_trace(candle, row=1, col=1)

    # ── 叠加指标（在主图上）──
    row_kw = dict(row=1, col=1) if n_rows > 1 else {}

    if "MA" in indicators:
        for win, color, name in [(20, "#FFA500", "MA20"), (60, "#4B9DFF", "MA60")]:
            ma = _calc_ma(df["close"], win)
            fig.add_trace(go.Scatter(
                x=x_data, y=ma, mode="lines",
                line=dict(color=color, width=1.2), name=name,
            ), **row_kw)

    if "BOLL" in indicators:
        upper, mid, lower = _calc_bollinger(df["close"])
        fig.add_trace(go.Scatter(
            x=x_data, y=upper, mode="lines",
            line=dict(color="#FF6B6B", width=1, dash="dash"),
            name="BOLL上轨",
        ), **row_kw)
        fig.add_trace(go.Scatter(
            x=x_data, y=mid, mode="lines",
            line=dict(color="#FFE66D", width=1), name="BOLL中轨",
        ), **row_kw)
        fig.add_trace(go.Scatter(
            x=x_data, y=lower, mode="lines",
            line=dict(color="#4ECDC4", width=1, dash="dash"),
            name="BOLL下轨",
        ), **row_kw)

    if "VWAP" in indicators and "volume" in df.columns:
        vwap = _calc_vwap(df)
        fig.add_trace(go.Scatter(
            x=x_data, y=vwap, mode="lines",
            line=dict(color="#E040FB", width=1.2, dash="dot"),
            name="VWAP",
        ), **row_kw)

    # ── 子面板指标 ──
    for panel_idx, panel in enumerate(sub_panels):
        row = 2 + panel_idx

        if panel == "RSI":
            rsi = _calc_rsi(df["close"], 14)
            fig.add_trace(go.Scatter(
                x=x_data, y=rsi, mode="lines",
                line=dict(color="#E040FB", width=1.2), name="RSI(14)",
            ), row=row, col=1)
            fig.add_hline(y=70, line_dash="dash",
                          line_color="rgba(255,75,75,0.5)", row=row, col=1)
            fig.add_hline(y=30, line_dash="dash",
                          line_color="rgba(0,200,83,0.5)", row=row, col=1)
            fig.update_yaxes(title_text="RSI", range=[0, 100], row=row, col=1)

        elif panel == "MACD":
            macd_line, signal_line, histogram = _calc_macd(df["close"])
            colors = [color_up if v >= 0 else color_down for v in histogram]
            fig.add_trace(go.Bar(
                x=x_data, y=histogram, marker_color=colors, name="MACD柱",
                opacity=0.6,
            ), row=row, col=1)
            fig.add_trace(go.Scatter(
                x=x_data, y=macd_line, mode="lines",
                line=dict(color="#4B9DFF", width=1.2), name="DIF",
            ), row=row, col=1)
            fig.add_trace(go.Scatter(
                x=x_data, y=signal_line, mode="lines",
                line=dict(color="#FFA500", width=1.2), name="DEA",
            ), row=row, col=1)
            fig.update_yaxes(title_text="MACD", row=row, col=1)

        elif panel == "KDJ":
            k, d, j = _calc_kdj(df)
            fig.add_trace(go.Scatter(
                x=x_data, y=k, mode="lines",
                line=dict(color="#4B9DFF", width=1.2), name="K",
            ), row=row, col=1)
            fig.add_trace(go.Scatter(
                x=x_data, y=d, mode="lines",
                line=dict(color="#FFA500", width=1.2), name="D",
            ), row=row, col=1)
            fig.add_trace(go.Scatter(
                x=x_data, y=j, mode="lines",
                line=dict(color="#E040FB", width=1.2), name="J",
            ), row=row, col=1)
            fig.update_yaxes(title_text="KDJ", row=row, col=1)

    # ── 布局 ──
    height = 450 if n_rows == 1 else 350 + 150 * len(sub_panels)
    fig.update_layout(
        title=title if n_rows == 1 else None,
        template="plotly_dark",
        height=height,
        xaxis_rangeslider_visible=False,
        margin=dict(l=50, r=20, t=50, b=30),
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1),
    )
    if n_rows > 1:
        fig.update_yaxes(title_text="价格", row=1, col=1)
        for i in range(1, n_rows + 1):
            fig.update_xaxes(rangeslider_visible=False, row=i, col=1)

    return fig


# ─── 成交量柱状图 ─────────────────────────────────────────

def create_volume_bar(df: pd.DataFrame, date_col: str = "date",
                      color_up: str = "#FF4B4B",
                      color_down: str = "#00C853") -> go.Figure:
    """创建成交量柱状图"""
    if df is None or df.empty:
        return go.Figure()

    vol_col = "volume" if "volume" in df.columns else "hold"
    if vol_col not in df.columns:
        return go.Figure()

    df = df.copy()
    if not pd.api.types.is_numeric_dtype(df["close"]):
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
    if not pd.api.types.is_numeric_dtype(df[vol_col]):
        df[vol_col] = pd.to_numeric(df[vol_col], errors="coerce")

    colors = []
    for i in range(len(df)):
        if i == 0:
            colors.append("#888888")
        elif df["close"].iloc[i] >= df["close"].iloc[i - 1]:
            colors.append(color_up)
        else:
            colors.append(color_down)

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
        xaxis_title="", yaxis_title="",
        xaxis_rangeslider_visible=False,
    )
    return fig


# ─── 持仓量趋势图 ─────────────────────────────────────────

def create_oi_chart(df: pd.DataFrame, date_col: str = "date",
                    color_up: str = "#FF4B4B",
                    color_down: str = "#00C853") -> go.Figure:
    """创建持仓量(OI)趋势图，含持仓变化柱状图"""
    if df is None or df.empty or "hold" not in df.columns:
        return go.Figure()

    df = df.copy()
    df["hold"] = pd.to_numeric(df["hold"], errors="coerce")

    x_data = df[date_col] if date_col in df.columns else df.index

    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.6, 0.4],
        subplot_titles=["持仓量", "持仓变化"],
    )

    # 持仓量线
    fig.add_trace(go.Scatter(
        x=x_data, y=df["hold"], mode="lines",
        line=dict(color="#4B9DFF", width=2), name="持仓量",
        fill="tozeroy", fillcolor="rgba(75,157,255,0.1)",
    ), row=1, col=1)

    # 持仓变化柱
    hold_change = df["hold"].diff()
    change_colors = [color_up if v >= 0 else color_down
                     for v in hold_change.fillna(0)]
    fig.add_trace(go.Bar(
        x=x_data, y=hold_change, marker_color=change_colors,
        name="持仓变化",
    ), row=2, col=1)

    fig.update_layout(
        template="plotly_dark", height=300,
        margin=dict(l=50, r=20, t=40, b=20),
        showlegend=False,
        xaxis2_rangeslider_visible=False,
    )
    return fig


# ─── 热力图 ───────────────────────────────────────────────

def create_heatmap(df: pd.DataFrame,
                   color_up: str = "#FF4B4B",
                   color_down: str = "#00C853") -> go.Figure:
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
            [0, color_down],
            [0.5, "#333333"],
            [1, color_up],
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


# ─── 迷你走势图 ──────────────────────────────────────────

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
        height=40, width=120,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    return fig


# ─── 折线图（宏观指标用）────────────────────────────────

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
        x=df[x_col], y=df[y_col],
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


# ─── 品种对比图（归一化叠加）─────────────────────────────

def create_comparison_chart(norm_df: pd.DataFrame,
                            title: str = "品种走势对比（归一化%）") -> go.Figure:
    """创建多品种归一化走势对比图"""
    if norm_df is None or norm_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="暂无数据", x=0.5, y=0.5,
                           xref="paper", yref="paper", showarrow=False,
                           font=dict(size=20, color="gray"))
        return fig

    colors = px.colors.qualitative.Set2
    fig = go.Figure()
    for i, col in enumerate(norm_df.columns):
        fig.add_trace(go.Scatter(
            x=list(range(len(norm_df))), y=norm_df[col],
            mode="lines",
            line=dict(color=colors[i % len(colors)], width=2),
            name=col,
        ))

    fig.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.3)")
    fig.update_layout(
        title=title,
        template="plotly_dark",
        height=500,
        xaxis_title="交易日",
        yaxis_title="涨跌幅 %",
        margin=dict(l=50, r=20, t=50, b=30),
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1),
    )
    return fig


# ─── 相关性矩阵热力图 ────────────────────────────────────

def create_correlation_heatmap(corr_df: pd.DataFrame,
                               title: str = "品种收益率相关性矩阵") -> go.Figure:
    """创建相关性矩阵热力图"""
    if corr_df is None or corr_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="暂无数据", x=0.5, y=0.5,
                           xref="paper", yref="paper", showarrow=False,
                           font=dict(size=20, color="gray"))
        return fig

    text_data = [[f"{v:.2f}" for v in row] for row in corr_df.values]

    fig = go.Figure(data=go.Heatmap(
        z=corr_df.values,
        x=corr_df.columns.tolist(),
        y=corr_df.index.tolist(),
        text=text_data,
        texttemplate="%{text}",
        textfont={"size": 11},
        colorscale="RdBu_r",
        zmid=0, zmin=-1, zmax=1,
        colorbar=dict(title="相关系数"),
    ))
    fig.update_layout(
        title=title,
        template="plotly_dark",
        height=max(350, 50 * len(corr_df)),
        margin=dict(l=100, r=20, t=50, b=80),
        xaxis=dict(tickangle=-45),
    )
    return fig


# ─── 价差走势图 ──────────────────────────────────────────

def create_spread_chart(spread_df: pd.DataFrame,
                        title: str = "价差走势") -> go.Figure:
    """创建价差走势图"""
    if spread_df is None or spread_df.empty or "spread" not in spread_df.columns:
        fig = go.Figure()
        fig.add_annotation(text="暂无数据", x=0.5, y=0.5,
                           xref="paper", yref="paper", showarrow=False,
                           font=dict(size=20, color="gray"))
        return fig

    fig = go.Figure()

    # 价差填充
    spread = spread_df["spread"]
    colors = ["rgba(255,75,75,0.3)" if v >= 0 else "rgba(0,200,83,0.3)"
              for v in spread]
    fig.add_trace(go.Bar(
        x=spread_df["date"], y=spread,
        marker_color=colors, name="价差",
    ))

    # MA20 of spread
    if len(spread) >= 20:
        ma = spread.rolling(20, min_periods=1).mean()
        fig.add_trace(go.Scatter(
            x=spread_df["date"], y=ma, mode="lines",
            line=dict(color="#FFE66D", width=1.5), name="MA20",
        ))

    fig.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.3)")
    fig.update_layout(
        title=title,
        template="plotly_dark",
        height=400,
        xaxis_title="日期",
        yaxis_title="价差",
        margin=dict(l=50, r=20, t=50, b=30),
    )
    return fig
