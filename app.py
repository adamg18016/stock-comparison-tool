import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Stock Comparison Tool",
    page_icon="📈",
    layout="wide"
)


# ============================================================
# COMPANY NAME → YAHOO FINANCE TICKER
# ============================================================

TICKER_MAP = {
    # US
    "APPLE": "AAPL",
    "MICROSOFT": "MSFT",
    "NVIDIA": "NVDA",
    "AMAZON": "AMZN",
    "META": "META",
    "GOOGLE": "GOOGL",
    "ALPHABET": "GOOGL",
    "TESLA": "TSLA",
    "JPMORGAN": "JPM",
    "JPMORGAN CHASE": "JPM",
    "GOLDMAN SACHS": "GS",
    "MORGAN STANLEY": "MS",
    "BLACKROCK": "BLK",
    "BERKSHIRE HATHAWAY": "BRK-B",

    # France
    "LVMH": "MC.PA",
    "HERMES": "RMS.PA",
    "HERMÈS": "RMS.PA",
    "L'OREAL": "OR.PA",
    "LOREAL": "OR.PA",
    "AIRBUS": "AIR.PA",
    "TOTALENERGIES": "TTE.PA",
    "BNP PARIBAS": "BNP.PA",
    "SOCIETE GENERALE": "GLE.PA",
    "SOCIÉTÉ GÉNÉRALE": "GLE.PA",
    "KERING": "KER.PA",
    "SCHNEIDER ELECTRIC": "SU.PA",
    "DASSAULT SYSTEMES": "DSY.PA",
    "DASSAULT SYSTÈMES": "DSY.PA",
    "AXA": "CS.PA",
    "VINCI": "DG.PA",
    "DANONE": "BN.PA",
    "CARREFOUR": "CA.PA",
    "ORANGE": "ORA.PA",
    "SAFRAN": "SAF.PA",
    "SAINT GOBAIN": "SGO.PA",
    "SAINT-GOBAIN": "SGO.PA",
    "VEOLIA": "VIE.PA",
    "CAPGEMINI": "CAP.PA",

    # Europe
    "ASML": "ASML.AS",
    "SAP": "SAP.DE",
    "SIEMENS": "SIE.DE",
    "ADIDAS": "ADS.DE",
    "BMW": "BMW.DE",
    "MERCEDES": "MBG.DE",
    "MERCEDES-BENZ": "MBG.DE",
    "VOLKSWAGEN": "VOW3.DE",
    "ALLIANZ": "ALV.DE",
    "DEUTSCHE BANK": "DBK.DE",
    "NOVO NORDISK": "NOVO-B.CO",
    "NESTLE": "NESN.SW",
    "NESTLÉ": "NESN.SW",
    "ROCHE": "ROG.SW",
    "UBS": "UBSG.SW",
    "UNILEVER": "ULVR.L",
    "BP": "BP.L",
    "SHELL": "SHEL.L",
    "HSBC": "HSBA.L",
    "ASTRAZENECA": "AZN.L",
}


# ============================================================
# FUNCTIONS
# ============================================================

def convert_to_ticker(input_name):
    """
    Converts a company name into a Yahoo Finance ticker.

    If the user enters a known company name:
        LVMH -> MC.PA

    If the user enters an actual Yahoo ticker:
        MC.PA -> MC.PA
    """

    cleaned = input_name.strip().upper()

    return TICKER_MAP.get(cleaned, cleaned)


def get_company_name(ticker):
    """
    Attempts to retrieve the company's long name from Yahoo Finance.
    """

    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        return info.get("longName", ticker)

    except Exception:
        return ticker


def download_data(tickers, period):
    """
    Downloads adjusted closing prices for all tickers.
    """

    data = yf.download(
        tickers,
        period=period,
        auto_adjust=True,
        progress=False
    )

    # Handle single ticker case
    if len(tickers) == 1:

        if "Close" in data.columns:
            data = data[["Close"]]
            data.columns = tickers

        elif "Adj Close" in data.columns:
            data = data[["Adj Close"]]
            data.columns = tickers

    # Handle multiple tickers
    else:

        if "Close" in data.columns:
            data = data["Close"]

        elif "Adj Close" in data.columns:
            data = data["Adj Close"]

    return data.dropna(how="all")


# ============================================================
# TITLE
# ============================================================

st.title("📈 Stock Comparison Tool")

st.markdown(
    """
Compare stocks across different markets using historical performance,
volatility, risk-adjusted returns and correlation.
"""
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("⚙️ Settings")

tickers_text = st.sidebar.text_input(
    "Enter companies or Yahoo Finance tickers",
    value="AAPL, LVMH, NVDA, GS",
    help=(
        "You can enter company names such as LVMH, Apple or NVIDIA, "
        "or Yahoo Finance tickers such as MC.PA, AAPL or NVDA."
    )
)

period = st.sidebar.selectbox(
    "Historical period",
    ["6mo", "1y", "2y", "5y", "10y"],
    index=1
)


# ============================================================
# PROCESS TICKERS
# ============================================================

raw_tickers = [
    t.strip()
    for t in tickers_text.split(",")
    if t.strip()
]

tickers = tuple(
    convert_to_ticker(t)
    for t in raw_tickers
)


# ============================================================
# SHOW TICKER CONVERSION
# ============================================================

if raw_tickers:

    with st.expander("🔎 Ticker mapping", expanded=False):

        mapping_df = pd.DataFrame({
            "Input": raw_tickers,
            "Yahoo Finance ticker": tickers
        })

        st.dataframe(
            mapping_df,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# VALIDATION
# ============================================================

if len(tickers) == 0:

    st.warning("Please enter at least one company or ticker.")

    st.stop()


if len(tickers) < 2:

    st.info(
        "Enter at least two stocks to compare performance and correlation."
    )


# ============================================================
# DOWNLOAD DATA
# ============================================================

with st.spinner("Downloading market data..."):

    try:

        data = download_data(tickers, period)

    except Exception as e:

        st.error(f"Could not download the data: {e}")

        st.stop()


# ============================================================
# CHECK DATA
# ============================================================

if data.empty:

    st.error(
        "No data was found. Check the company names or Yahoo Finance tickers."
    )

    st.stop()


# Remove completely empty columns

data = data.dropna(axis=1, how="all")


# Find valid tickers

valid_tickers = list(data.columns)


if len(valid_tickers) == 0:

    st.error("No valid stocks were found.")

    st.stop()


# ============================================================
# COMPANY NAMES
# ============================================================

company_names = {}

with st.spinner("Loading company information..."):

    for ticker in valid_tickers:

        company_names[ticker] = get_company_name(ticker)


# ============================================================
# DISPLAY VALID STOCKS
# ============================================================

st.subheader("Stocks loaded")

display_df = pd.DataFrame({
    "Company": [
        company_names[ticker]
        for ticker in valid_tickers
    ],
    "Yahoo Ticker": valid_tickers
})

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# TOTAL RETURNS
# ============================================================

returns = data.pct_change().dropna()


total_returns = (
    data.iloc[-1] / data.iloc[0] - 1
) * 100


# ============================================================
# ANNUALIZED VOLATILITY
# ============================================================

annualized_volatility = (
    returns.std() * (252 ** 0.5)
) * 100


# ============================================================
# RETURN / RISK
# ============================================================

return_risk = (
    total_returns / annualized_volatility
)


# ============================================================
# METRICS TABLE
# ============================================================

st.subheader("📊 Performance & Risk")

metrics_df = pd.DataFrame({
    "Company": [
        company_names[ticker]
        for ticker in valid_tickers
    ],
    "Ticker": valid_tickers,
    "Total Return (%)": total_returns.values,
    "Annualized Volatility (%)": annualized_volatility.values,
    "Return / Risk": return_risk.values
})

metrics_df = metrics_df.round(2)

st.dataframe(
    metrics_df,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# PORTFOLIO STATISTICS
# ============================================================

if len(valid_tickers) >= 2:

    st.subheader("💼 Equal-Weight Portfolio")

    portfolio_returns = returns.mean(axis=1)

    portfolio_total_return = (
        (1 + portfolio_returns).prod() - 1
    ) * 100

    portfolio_volatility = (
        portfolio_returns.std() * (252 ** 0.5)
    ) * 100

    portfolio_return_risk = (
        portfolio_total_return / portfolio_volatility
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Portfolio Return",
        f"{portfolio_total_return:.2f}%"
    )

    col2.metric(
        "Portfolio Volatility",
        f"{portfolio_volatility:.2f}%"
    )

    col3.metric(
        "Return / Risk",
        f"{portfolio_return_risk:.2f}"
    )


# ============================================================
# GROWTH OF €100
# ============================================================

st.subheader("💰 Growth of €100")

normalized_data = (
    data / data.iloc[0]
) * 100

fig, ax = plt.subplots(figsize=(12, 6))

for ticker in valid_tickers:

    ax.plot(
        normalized_data.index,
        normalized_data[ticker],
        label=company_names[ticker]
    )

ax.set_xlabel("Date")
ax.set_ylabel("Portfolio Value (€)")
ax.set_title("Growth of €100")

ax.legend()

ax.grid(True, alpha=0.3)

plt.tight_layout()

st.pyplot(fig)


# ============================================================
# CORRELATION
# ============================================================

if len(valid_tickers) >= 2:

    st.subheader("🔗 Stock Correlation")

    correlation = returns.corr()

    # Replace ticker labels with company names
    correlation_display = correlation.copy()

    correlation_display.index = [
        company_names[ticker]
        for ticker in correlation.index
    ]

    correlation_display.columns = [
        company_names[ticker]
        for ticker in correlation.columns
    ]

    fig, ax = plt.subplots(
        figsize=(10, 7)
    )

    im = ax.imshow(
        correlation_display,
        aspect="auto"
    )

    ax.set_xticks(
        range(len(correlation_display.columns))
    )

    ax.set_yticks(
        range(len(correlation_display.index))
    )

    ax.set_xticklabels(
        correlation_display.columns,
        rotation=45,
        ha="right"
    )

    ax.set_yticklabels(
        correlation_display.index
    )

    # Add correlation numbers
    for i in range(len(correlation_display.index)):

        for j in range(len(correlation_display.columns)):

            ax.text(
                j,
                i,
                f"{correlation_display.iloc[i, j]:.2f}",
                ha="center",
                va="center"
            )

    ax.set_title("Correlation Matrix")

    plt.colorbar(im, ax=ax)

    plt.tight_layout()

    st.pyplot(fig)


# ============================================================
# PRICE DATA
# ============================================================

with st.expander("📋 Historical Price Data"):

    historical_display = data.copy()

    historical_display.columns = [
        company_names[ticker]
        for ticker in historical_display.columns
    ]

    st.dataframe(
        historical_display,
        use_container_width=True
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "By AGrahamC • Data provided by Yahoo Finance via yfinance"
)
