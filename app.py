import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime

st.title("Dashboard Bovespa")

def build_sidebar():
    st.image("images/logo-250-100-transparente.png")
    # Lê o CSV como está (sem cabeçalho)
    ticker_list = pd.read_csv("tickers_ibra.csv", header=None)
    tickers_options = ticker_list[1].tolist()  # coluna 1 = tickers

    # Tickes padrão
    default_tickers = [t for t in ["PETR4", "SUZ3", "PRIO3"] if t in tickers_options]

    tickers = st.multiselect(
        label="Selecione os tickers",
        options=tickers_options,
        default=default_tickers,
        placeholder="Escolha as opções"
    )

    start_date = st.date_input("De", value=datetime(2020, 1, 1))
    end_date = st.date_input("Até", value=datetime.today())

    return tickers, start_date, end_date

def get_prices(tickers, start_date, end_date):
    if tickers:
        tickers_yf = [t + ".SA" for t in tickers]
        prices_raw = yf.download(tickers_yf, start=start_date, end=end_date)
        # Trata 1 ou vários tickers
        if "Adj Close" in prices_raw:
            prices = prices_raw["Adj Close"]
        elif "Adj Close" in prices_raw.columns:
            prices = prices_raw[["Adj Close"]]
            prices.columns = [tickers_yf[0]]
        else:
            prices = pd.DataFrame()
        return prices
    return pd.DataFrame()

with st.sidebar:
    tickers, start_date, end_date = build_sidebar()

prices = get_prices(tickers, start_date, end_date)

# MAIN PAGE
if not prices.empty:
    st.dataframe(prices)
else:
    st.info("Selecione ao menos um ticker para exibir os preços.")
