import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Stock Comparison Tool", layout="wide")
st.markdown(
    """
    <style>
    .watermark {
        position: fixed;
        bottom: 8px;
        right: 12px;
        font-size: 12px;
        color: rgba(120, 120, 120, 0.6);
        z-index: 100;
    }
    </style>
    <div class="watermark">By AGrahamC</div>
    """,
    unsafe_allow_html=True,
)
st.title("Stock Comparison Tool")
st.write("Compare the performance, risk and correlation of any listed companies, "
         "and see how an equal-weight portfolio of them would have behaved.")

# ---------- INPUTS ----------
tickers_text = st.text_input(
    "Stock tickers, separated by commas",
    value="AAPL, NET, GS, NVDA",
    help="Use tickers, not company names. Example: AAPL = Apple, NET = Cloudflare, "
         "GS = Goldman Sachs, NVDA = Nvidia.",
)
period = st.selectbox("Time period", ["6mo", "1y", "2y", "5y", "10y"], index=1)
run = st.button("Run analysis")


# ---------- DATA ----------
@st.cache_data(show_spinner=False)
def get_prices(tickers, period):
    """Download daily prices (adjusted for dividends and splits)."""
    data = yf.download(list(tickers), period=period, auto_adjust=True, progress=False)["Close"]
    if isinstance(data, pd.Series):
        data = data.to_frame(name=tickers[0])
    return data


# ---------- ANALYSIS ----------
if run:
    tickers = tuple(dict.fromkeys(t.strip().upper() for t in tickers_text.split(",") if t.strip()))

    if len(tickers) < 2:
        st.error("Enter at least two tickers so the comparison and correlation make sense.")
        st.stop()

    with st.spinner("Downloading market data..."):
        prices = get_prices(tickers, period)

    # Drop tickers that returned no data (wrong ticker or delisted)
    missing = [t for t in tickers if t not in prices.columns or prices[t].dropna().empty]
    if missing:
        st.warning(f"No data found for: {', '.join(missing)}. Check the ticker spelling.")
    prices = prices.drop(columns=[c for c in missing if c in prices.columns]).dropna()

    if prices.shape[1] < 2 or len(prices) < 20:
        st.error("Not enough valid data to run the analysis. Try different tickers or a longer period.")
        st.stop()

    # Daily returns = percentage change in price from one day to the next
    returns = prices.pct_change().dropna()

    # Key metrics
    total_return = (prices.iloc[-1] / prices.iloc[0] - 1) * 100
    volatility = returns.std() * (252 ** 0.5) * 100   # annualised (252 trading days)
    return_per_risk = total_return / volatility

    summary = pd.DataFrame({
        "Total return (%)": total_return.round(1),
        "Volatility (%)": volatility.round(1),
        "Return / risk": return_per_risk.round(2),
    }).sort_values("Total return (%)", ascending=False)

    # Equal-weight portfolio (same amount invested in each stock)
    portfolio_daily = returns.mean(axis=1)
    portfolio_growth = (1 + portfolio_daily).cumprod() * 100   # starts at 100
    portfolio_return = portfolio_growth.iloc[-1] - 100
    portfolio_vol = portfolio_daily.std() * (252 ** 0.5) * 100

    # ---------- DISPLAY ----------
    st.subheader("Summary")
    st.dataframe(summary, width="stretch")

    c1, c2 = st.columns(2)
    c1.metric("Equal-weight portfolio return", f"{portfolio_return:.1f}%")
    c2.metric("Equal-weight portfolio volatility", f"{portfolio_vol:.1f}%")

    left, right = st.columns(2)

    with left:
        st.subheader("Growth of 100 invested")
        fig1, ax1 = plt.subplots(figsize=(7, 4.5))
        (prices / prices.iloc[0] * 100).plot(ax=ax1)
        portfolio_growth.plot(ax=ax1, color="black", linewidth=3, label="Portfolio")
        ax1.set_ylabel("Value")
        ax1.legend()
        st.pyplot(fig1)

    with right:
        st.subheader("Correlation of daily returns")
        corr = returns.corr()
        fig2, ax2 = plt.subplots(figsize=(6, 4.5))
        im = ax2.imshow(corr, cmap="coolwarm", vmin=-1, vmax=1)
        ax2.set_xticks(range(len(corr)))
        ax2.set_xticklabels(corr.columns, rotation=45)
        ax2.set_yticks(range(len(corr)))
        ax2.set_yticklabels(corr.columns)
        fig2.colorbar(im, ax=ax2, label="Correlation")
        st.pyplot(fig2)

    st.caption("Volatility = annualised standard deviation of daily returns (a measure of risk). "
               "Correlation close to 1 means stocks move together; lower values mean better diversification. "
               "Data: Yahoo Finance via yfinance. Past performance does not predict future results.")
