import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px
from datetime import datetime, date
from streamlit_extras.metric_cards import style_metric_cards
from streamlit_extras.grid import grid

def build_sidebar():
    st.image("images/logo-250-100-transparente.png")

    # ─── Leitura do CSV de tickers ───────────────────────────────────
    tickers_df = pd.read_csv(
        "tickers_ibra.csv",
        skiprows=1,
        header=None,
        names=["idx", "ticker"]
    )
    lista_tickers = tickers_df["ticker"].tolist()

    # ─── Pré‑seleção padrão ───────────────────────────────────────────
    default_selection = [t for t in ["SUZB3", "PETR4"] if t in lista_tickers]

    selecionados = st.multiselect(
        label="Selecione as Empresas",
        options=lista_tickers,
        default=default_selection,
        placeholder="Códigos"
    )
    tickers = [f"{t}.SA" for t in selecionados]

    # ─── Inputs de data ────────────────────────────────────────────────
    start_date = st.date_input(
        "De",
        format="DD/MM/YYYY",
        value=datetime(2023, 1, 2)
    )
    end_date = st.date_input(
        "Até",
        format="DD/MM/YYYY",
        value=date.today()
    )

    if not tickers:
        return None, None

    # ─── Download de preços ajustados usando Close ─────────────────────
    raw = yf.download(
        tickers,
        start=start_date,
        end=end_date,
        auto_adjust=True,       # ajusta splits e dividendos
        group_by="column",
        progress=False
    )
    try:
        prices = raw["Close"]
    except KeyError:
        prices = raw.xs("Close", axis=1, level=1)

    prices.columns = prices.columns.str.rstrip(".SA")

    # ─── Download do IBOV ──────────────────────────────────────────────
    raw_ibov = yf.download(
        "^BVSP",
        start=start_date,
        end=end_date,
        auto_adjust=True,
        group_by="column",
        progress=False
    )
    try:
        ibov = raw_ibov["Close"]
    except KeyError:
        ibov = raw_ibov.xs("Close", axis=1, level=1)

    prices["IBOV"] = ibov

    return tickers, prices

def build_main(tickers, prices):
    weights = np.ones(len(tickers)) / len(tickers)
    prices["portfolio"] = prices.drop("IBOV", axis=1) @ weights

    norm_prices = 100 * prices / prices.iloc[0]
    returns = prices.pct_change().dropna()
    vols = returns.std() * np.sqrt(252)
    rets = (norm_prices.iloc[-1] - 100) / 100

    mygrid = grid(5, 5, 5, 5, 5, 5, vertical_align="top")
    for t in prices.columns:
        c = mygrid.container(border=True)
        c.subheader(t, divider="red")
        colA, colB, colC = c.columns(3)
        if t == "portfolio":
            colA.image("images/pie-chart-dollar-svgrepo-com.svg")
        elif t == "IBOV":
            colA.image("images/pie-chart-svgrepo-com.svg")
        else:
            colA.image(
                f"https://raw.githubusercontent.com/thefintz/icones-b3/main/icones/{t}.png",
                width=85
            )
        colB.metric(label="Retorno", value=f"{rets[t]:.0%}")
        colC.metric(label="Volatilidade", value=f"{vols[t]:.0%}")
        style_metric_cards(background_color="rgba(255,255,255,0)")

    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.subheader("Desempenho Relativo")
        st.line_chart(norm_prices, height=600)

    with col2:
        st.subheader("Risco-Retorno")
        fig = px.scatter(
            x=vols,
            y=rets,
            text=vols.index,
            color=rets / vols,
            color_continuous_scale=px.colors.sequential.Bluered_r
        )
        fig.update_traces(
            textfont_color="white",
            marker=dict(size=45),
            textfont_size=10,
        )
        fig.layout.xaxis.title = "Volatilidade (anualizada)"
        fig.layout.yaxis.title = "Retorno Total"
        fig.layout.xaxis.tickformat = ".0%"
        fig.layout.yaxis.tickformat = ".0%"
        fig.layout.coloraxis.colorbar.title = "Sharpe"
        fig.layout.height = 600
        st.plotly_chart(fig, use_container_width=True)

# ─── Configuração de página ─────────────────────────────────────────
st.set_page_config(layout="wide")

with st.sidebar:
    tickers, prices = build_sidebar()

st.title("Python para Investidores")
if tickers and prices is not None:
    build_main(tickers, prices)
