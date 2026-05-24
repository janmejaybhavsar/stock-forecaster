import plotly.graph_objects as go
from plotly.subplots import make_subplots


def candlestick_chart(data: list[dict], title: str = "") -> go.Figure:
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.7, 0.3],
        subplot_titles=[title, "Volume"],
    )

    dates = [d["date"] for d in data]
    fig.add_trace(
        go.Candlestick(
            x=dates,
            open=[d["open"] for d in data],
            high=[d["high"] for d in data],
            low=[d["low"] for d in data],
            close=[d["close"] for d in data],
            name="Price",
        ),
        row=1, col=1,
    )

    colors = []
    for i, d in enumerate(data):
        colors.append("#26a69a" if d["close"] >= d["open"] else "#ef5350")

    fig.add_trace(
        go.Bar(
            x=dates,
            y=[d["volume"] for d in data],
            marker_color=colors,
            name="Volume",
            showlegend=False,
        ),
        row=2, col=1,
    )

    fig.update_layout(
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        height=600,
        margin=dict(l=50, r=50, t=50, b=30),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    fig.update_yaxes(title_text="Price ($)", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)

    return fig


def forecast_chart(
    historical: list[dict],
    predictions: list[dict],
    title: str = "Price Forecast",
) -> go.Figure:
    fig = go.Figure()

    hist_dates = [d["date"] for d in historical]
    hist_close = [d["close"] for d in historical]
    fig.add_trace(go.Scatter(
        x=hist_dates, y=hist_close,
        mode="lines", name="Historical",
        line=dict(color="#42a5f5", width=2),
    ))

    pred_dates = [p["date"] for p in predictions]
    pred_close = [p["predicted_close"] for p in predictions]
    pred_lower = [p["lower_bound"] for p in predictions]
    pred_upper = [p["upper_bound"] for p in predictions]

    fig.add_trace(go.Scatter(
        x=pred_dates, y=pred_upper,
        mode="lines", line=dict(width=0),
        showlegend=False,
    ))
    fig.add_trace(go.Scatter(
        x=pred_dates, y=pred_lower,
        mode="lines", line=dict(width=0),
        fill="tonexty",
        fillcolor="rgba(255,167,38,0.2)",
        name="Confidence Band",
    ))
    fig.add_trace(go.Scatter(
        x=pred_dates, y=pred_close,
        mode="lines+markers", name="Forecast",
        line=dict(color="#ffa726", width=2, dash="dash"),
    ))

    fig.update_layout(
        title=title,
        template="plotly_dark",
        height=500,
        margin=dict(l=50, r=50, t=50, b=30),
        yaxis_title="Price ($)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    return fig


def comparison_bar_chart(metrics_by_model: dict[str, dict]) -> go.Figure:
    model_names = list(metrics_by_model.keys())
    metric_names = ["MAE", "RMSE", "MAPE", "Directional Accuracy"]

    fig = go.Figure()
    colors = ["#42a5f5", "#66bb6a", "#ffa726", "#ab47bc"]

    for i, metric in enumerate(metric_names):
        key = metric.lower().replace(" ", "_")
        values = [metrics_by_model[m].get(key, 0) for m in model_names]
        fig.add_trace(go.Bar(
            name=metric, x=model_names, y=values,
            marker_color=colors[i % len(colors)],
        ))

    fig.update_layout(
        title="Model Comparison",
        barmode="group",
        template="plotly_dark",
        height=400,
        margin=dict(l=50, r=50, t=50, b=30),
    )
    return fig


def equity_curve_chart(equity_data: list[dict]) -> go.Figure:
    fig = go.Figure()

    dates = [d["date"] for d in equity_data]
    fig.add_trace(go.Scatter(
        x=dates,
        y=[d.get("strategy", d.get("cumulative_return", 0)) for d in equity_data],
        mode="lines", name="Model Strategy",
        line=dict(color="#ffa726", width=2),
    ))

    if "buy_hold" in equity_data[0]:
        fig.add_trace(go.Scatter(
            x=dates,
            y=[d["buy_hold"] for d in equity_data],
            mode="lines", name="Buy & Hold",
            line=dict(color="#42a5f5", width=2, dash="dash"),
        ))

    fig.update_layout(
        title="Equity Curve",
        template="plotly_dark",
        height=400,
        yaxis_title="Cumulative Return",
        margin=dict(l=50, r=50, t=50, b=30),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    return fig
