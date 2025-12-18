import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from fredapi import Fred
import yfinance as yf
from datetime import datetime

# Fonction de formattage des données 
    # Ajout de la fonction de formatage des grands nombres
def format_number(x):
    if x is None:
        return "N/A"
    try:
        x = float(x)
        if x >= 1e9:
            return f"{x/1e9:.2f}B"
        elif x >= 1e6:
            return f"{x/1e6:.2f}M"
        elif x >= 1e3:
            return f"{x/1e3:.2f}K"
        else:
            return f"{x:.2f}"
    except:
        return str(x)
    
    # Fonction pour supprimer les heures des index de date
def clean_index(df):
    df_clean = df.copy()
    df_clean.index = pd.to_datetime(df_clean.index).date
    return df_clean

# Configuration de la page
st.set_page_config(
    page_title="Hirsch Capital - Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)
# =================== STYLES GÉNÉRAUX (CSS) ===================
st.markdown("""
<style>
/* =================== Fond général =================== */
.main, .stApp {
    background-color: #0A1929;
}

/* =================== Texte global =================== */
h1, h2, h3, h4, h5, h6, p, span, div, label {
    color: #FFFFFF !important;
}

/* =================== Cards cliquables =================== */
.metric-card {
    background: linear-gradient(135deg, #1e3a5f 0%, #2a5298 100%);
    padding: 30px;
    border-radius: 15px;
    border-left: 5px solid #4FC3F7;
    margin: 15px 0;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
}
.metric-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 15px rgba(79, 195, 247, 0.4);
    border-left: 5px solid #81D4FA;
}
.metric-card h3 {
    color: #FFFFFF !important;
    font-size: 1.5em;
    margin-bottom: 10px;
}
.metric-card p {
    color: #B0BEC5 !important;
    font-size: 0.9em;
}

/* =================== Métriques =================== */
.stMetric {
    background: linear-gradient(135deg, #1e3a5f 0%, #2a5298 100%);
    padding: 20px;
    border-radius: 12px;
    border-left: 4px solid #4FC3F7;
}
.stMetric label {
    color: #B0BEC5 !important;
    font-size: 0.9em;
}
.stMetric [data-testid="stMetricValue"] {
    color: #FFFFFF !important;
    font-size: 1.8em;
    font-weight: bold;
}
.stMetric [data-testid="stMetricDelta"] {
    font-size: 1em;
}

/* =================== Sidebar =================== */
[data-testid="stSidebar"] {
    background-color: #0d2137;
}
[data-testid="stSidebar"] * {
    color: #FFFFFF !important;
}

/* =================== Tabs =================== */
.stTabs [data-baseweb="tab-list"] {
    background-color: #132F4C;
    border-radius: 10px;
    padding: 5px;
}
.stTabs [data-baseweb="tab"] {
    color: #B0BEC5 !important;
    background-color: transparent;
    border-radius: 8px;
}
.stTabs [aria-selected="true"] {
    background-color: #1e3a5f !important;
    color: #FFFFFF !important;
}

/* =================== Boutons =================== */
.stButton button {
    background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 25px;
    font-weight: bold;
}
.stButton button:hover {
    background: linear-gradient(135deg, #1976D2 0%, #1565C0 100%);
    box-shadow: 0 4px 12px rgba(33, 150, 243, 0.4);
}

/* =================== Selectbox =================== */
div[data-testid="stSelectbox"] label,
div[data-testid="stSidebar"] div[data-testid="stSelectbox"] label {
    color: #FFFFFF !important;
    font-weight: bold;
}
div[data-testid="stSelectbox"] > div[role="combobox"],
div[data-testid="stSidebar"] div[data-testid="stSelectbox"] > div[role="combobox"],
div[data-baseweb="select"] {
    color: #FFFFFF !important;
    background-color: #132F4C !important;
    border-radius: 8px !important;
    border: 1px solid #4FC3F7 !important;
}
/* =================== Text Input =================== */
div[data-testid="stTextInput"] label {
    color: #FFFFFF !important;
    font-weight: bold;
}
div[data-testid="stTextInput"] input {
    background-color: #132F4C !important;
    color: #FFFFFF !important;
    border-radius: 8px;
    border: 1px solid #4FC3F7;
}

/* =================== Info boxes =================== */
.info-box {
    background-color: #132F4C;
    border-left: 4px solid #4FC3F7;
    padding: 15px;
    border-radius: 8px;
    margin: 10px 0;
}
.info-box p {
    color: #B0BEC5 !important;
    margin: 0;
    font-size: 0.85em;
    line-height: 1.6;
}

/* =================== DataFrame =================== */
.dataframe-container table {
    background-color: #0A1929 !important; /* fond du tableau */
    color: white !important;              /* texte */
    border-collapse: collapse;            /* éviter double bordures */
    width: 100%;                          /* occuper toute la largeur */
}

.dataframe-container th, 
.dataframe-container td {
    border: 2px solid white !important;   /* bordures plus visibles */
    padding: 5px;
    text-align: right;                     /* aligner chiffres à droite */
}

.dataframe-container th {
    background-color: #0A1929 !important; /* même fond pour header */
    font-weight: bold;
}

/* =================== Dividers =================== */
hr {
    border-color: #2a5298;
}
</style>
""", unsafe_allow_html=True)


# Initialisation FRED API
@st.cache_resource
def init_fred():
    return Fred(api_key='2d1c543149c61f38630e0e0ff35d539c')

fred = init_fred()

# Mapping des devises par pays
COUNTRY_CURRENCIES = {
    'USA': 'USD',
    'France': 'EUR',
    'Germany': 'EUR',
    'UK': 'GBP',
    'China': 'CNY',
    'Japan': 'JPY',
    'Switzerland': 'CHF'
}

# Fonctions de récupération des données
@st.cache_data(ttl=3600)
def get_gdp_data(countries, period='5Y'):
    gdp_series = {
        'USA': 'GDP',
        'France': 'CPMNACSCAB1GQFR',
        'UK': 'UKNGDP',
        'Germany': 'CPMNACSCAB1GQDE',
        'Japan': 'JPNNGDP',
        'China': 'MKTGDPCNA646NWDB'
    }
    
    data = {}
    variations = {}
    
    for country in countries:
        if country in gdp_series:
            series = fred.get_series(gdp_series[country])
            data[country] = series
            variations[country] = {
                'QoQ': round(series.pct_change().iloc[-1] * 100, 2),
                'YoY': round(series.pct_change(4).iloc[-1] * 100, 2)
            }
    
    return data, variations

@st.cache_data(ttl=3600)
def get_cpi_data(countries):
    cpi_series = {
        'USA': 'CPIAUCSL',
        'France': 'CP0000FRM086NEST',
        'UK': 'CP0000GBM086NEST',
        'Germany': 'CP0000DEM086NEST',
        'Japan': 'CPALTT01JPM657N',
        'China': 'CPALTT01CNM657N'
    }
    
    data = {}
    variations = {}
    
    for country in countries:
        if country in cpi_series:
            series = fred.get_series(cpi_series[country])
            data[country] = series
            variations[country] = {
                'MoM': round(series.pct_change().iloc[-1] * 100, 2),
                'YoY': round(series.pct_change(12).iloc[-1] * 100, 2)
            }
    
    return data, variations
@st.cache_data(ttl=3600)

def unemployment_rate():
    unemp_series = {
        'USA': 'UNRATE',                 # US Unemployment Rate
        'Europe': 'LRHUTTTTEUM156S'      # Euro Area Unemployment Rate
    }
    
    data = {}
    summary = {}
    
    for region, series_id in unemp_series.items():
        series = fred.get_series(series_id, observation_start='2000-01-01')
        data[region] = series
        
        summary[region] = {
            'value': round(series.iloc[-1], 2),
            'variation': round(series.pct_change().iloc[-1] * 100, 2)
        }
    return data, summary

@st.cache_data(ttl=3600)
def get_forex_data(pairs, period='1y'):
    forex_tickers = {
        'EURUSD': 'EURUSD=X',
        'GBPUSD': 'GBPUSD=X',
        'USDJPY': 'JPY=X',
        'USDCNY': 'CNY=X',
        'USDCHF': 'CHF=X'
    }
    
    data = {}
    summary = {}
    
    for pair in pairs:
        if pair in forex_tickers:
            ticker_data = yf.Ticker(forex_tickers[pair]).history(period=period)['Close']
            data[pair] = ticker_data
            
            var_1w = ticker_data.pct_change(5).iloc[-1] * 100
            var_1m = ticker_data.pct_change(21).iloc[-1] * 100
            
            summary[pair] = {
                'value': round(ticker_data.iloc[-1], 4),
                'var_1w': round(var_1w, 2),
                'var_1m': round(var_1m, 2)
            }
    
    return data, summary

@st.cache_data(ttl=3600)
def get_commodities_data(period='1y'):
    gold = yf.Ticker("GC=F").history(period=period)['Close']
    oil = yf.Ticker("CL=F").history(period=period)['Close']
    
    return {
        'Gold': gold,
        'Oil': oil
    }

@st.cache_data(ttl=3600)
def get_interest_rates():
    us_fed = fred.get_series('EFFR') 
    euro_ecb = fred.get_series('ECBESTRVOLWGTTRMDMNRT') 
    
    return {
        'US_Fed': us_fed,
        'Euro_ECB': euro_ecb
    }

@st.cache_data(ttl=3600)
def get_bond_rates(countries):
    bond_series = {
        'USA': 'DGS10',
        'Germany': 'IRLTLT01DEM156N',
        'France': 'IRLTLT01FRM156N',
        'UK': 'IRLTLT01GBM156N',
        'Japan': 'IRLTLT01JPM156N'
    }
    
    data = {}
    summary = {}
    
    for country in countries:
        if country in bond_series:
            series = fred.get_series(bond_series[country])
            data[country] = series
            summary[country] = {
                'value': round(series.iloc[-1], 2),
                'variation': round(series.pct_change().iloc[-1] * 100, 2)
            }
    
    return data, summary

@st.cache_data(ttl=3600)
def get_yield_curve(country):
    """Récupère la courbe des taux pour un pays"""
    maturities = {
        'USA': {
            '1M': 'DGS1MO', '3M': 'DGS3MO', '6M': 'DGS6MO',
            '1Y': 'DGS1', '2Y': 'DGS2', '5Y': 'DGS5',
            '7Y': 'DGS7', '10Y': 'DGS10', '20Y': 'DGS20', '30Y': 'DGS30'
        }
    }
    
    if country not in maturities:
        return None
    
    curve_data = {}
    for maturity, code in maturities[country].items():
        try:
            series = fred.get_series(code)
            if series is not None and len(series) > 0:
                curve_data[maturity] = series.iloc[-1]
        except:
            pass
    
    return curve_data

# Fonction pour déterminer les paires forex nécessaires
def get_required_forex_pairs(countries):
    currencies = set()
    for country in countries:
        if country in COUNTRY_CURRENCIES:
            currencies.add(COUNTRY_CURRENCIES[country])
    
    pairs = []
    if 'EUR' in currencies:
        pairs.append('EURUSD')
    if 'GBP' in currencies:
        pairs.append('GBPUSD')
    if 'JPY' in currencies:
        pairs.append('USDJPY')
    if 'CNY' in currencies:
        pairs.append('USDCNY')
    if 'CHF' in currencies:
        pairs.append('USDCHF')
    
    return pairs

# ========== HEADER ==========
col1, col2 = st.columns([3, 1])
with col1:
    st.title("Hirsch Capital - Dashboard ")
with col2:
    st.markdown(f"<div style='text-align: right; padding-top: 20px; color: #B0BEC5;'>Mise à jour: {datetime.now().strftime('%d/%m/%Y %H:%M')}</div>", unsafe_allow_html=True)

st.markdown("---")

# ========== SIDEBAR (attention à la lisibilité du champ avec les couleurs d'ecriture) ==========
with st.sidebar:
    st.markdown("#### Sidebar Settings")
    
    # Période d'analyse 
    st.markdown("#### 📅 Analysis Period")
    period_options = {
        '1 Jour': '1d',
        '5 Jours': '5d',
        '1 Mois': '1mo',
        '3 Mois': '3mo',
        '6 Mois': '6mo',
        'Année en cours': 'ytd',
        '1 An': '1y',
        '2 Ans': '2y',
        '5 Ans': '5y',
        '10 Ans': '10y',
        'Max': 'max'
    }
    selected_period_label = st.selectbox(
        "Period",
        list(period_options.keys()),
        index=2,
        label_visibility="collapsed"
    )
    selected_period = period_options[selected_period_label]

    st.markdown("---")
    
    # Avertissements
    st.markdown("""
    <div class='info-box'>
        <p><strong>⚠️ Update frequencies:</strong></p>
        <p>• GDP: Quarterly data</p>
        <p>• CPI: Monthly data</p>
        <p>• Bonds: Monthly data</p>
    </div>
    """, unsafe_allow_html=True)

# ========== NAVIGATION ==========
# Session state pour la navigation
if 'page' not in st.session_state:
    st.session_state.page = 'home'

# Page d'accueil avec les cards cliquables
if st.session_state.page == 'home':
    st.markdown("## Home Page")
    st.markdown("### Select a section to explore:")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("GDP, CPI & Unemployment", use_container_width=True, key="btn_gdp"):
            st.session_state.page = 'gdp_cpi'
            st.rerun()
        st.markdown("""
        <div class='info-box'>
            <p>Analyze economic growth and inflation by country</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if st.button("Forex & Commodities", use_container_width=True, key="btn_forex"):
            st.session_state.page = 'forex_commodities'
            st.rerun()
        st.markdown("""
        <div class='info-box'>
            <p>Evolution of exchange rates and commodities</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        if st.button("Rates & Bonds", use_container_width=True, key="btn_rates"):
            st.session_state.page = 'rates_bonds'
            st.rerun()
        st.markdown("""
        <div class='info-box'>
            <p>Interest rates and sovereign bonds</p>
        </div>
        """, unsafe_allow_html=True)
    
    col4 = st.columns(1)[0]
    
    with col4:
        if st.button("Equity Analysis Suite", use_container_width=True, key="btn_equity"):
            st.session_state.page = 'equity_suite'
            st.rerun()
        st.markdown("""
        <div class='info-box'>
             <p>Complete analysis of a ticker, correlations and financial statements</p>
        </div>
        """, unsafe_allow_html=True)


# ========== PAGE GDP & CPI & UNEMPLOYMENT ==========
elif st.session_state.page == 'gdp_cpi':
    col1, col2 = st.columns([6, 1])
    with col1:
        st.markdown("## GDP,CPI & Unemployment Rate")
    with col2:
        if st.button("Back", use_container_width=True):
            st.session_state.page = 'home'
            st.rerun()
    
    st.markdown("""
    <div class='info-box'>
        <p><strong>💡 How to interpret these data :</strong></p>
        <p>• <strong>GDP (Gross)</strong> : Measures the economic growth of a country. An increase indicates expansion, a decrease contraction.</p>
        <p>• <strong>CPI (Consumer Price Index)</strong> : Measures inflation. An increase indicates a rise in consumption prices.</p>
        <p>• <strong>Unemployment Rate</strong> : Measures the unemployment rate. An increase indicates a rise in the number of unemployed people.</p>
        <p>• <strong>QoQ</strong> = Variation compared to the previous quarter | <strong>YoY</strong> = Variation over 1 year</p>
        <p>• <strong>MoM</strong> = Variation compared to the previous month</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("#### 🌍 SSelection of countries")
    macro_countries = st.multiselect(
    "Choose the countries to analyze",
    ['USA', 'France', 'Germany', 'UK', 'China', 'Japan'],
    default=['USA', 'France', 'Germany', 'UK'])
    
    # Récupération des données
    gdp_data, gdp_variations = get_gdp_data(macro_countries, selected_period)
    cpi_data, cpi_variations = get_cpi_data(macro_countries)
    unemp_data, unemp_summary = unemployment_rate()

    
    # Bar charts côte à côte
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### GDP Variations")
        
        # Préparer les données pour le graphique
        gdp_countries = list(gdp_variations.keys())
        gdp_qoq = [gdp_variations[c]['QoQ'] for c in gdp_countries]
        gdp_yoy = [gdp_variations[c]['YoY'] for c in gdp_countries]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=gdp_countries,
            y=gdp_qoq,
            name='QoQ',
            marker_color='#4FC3F7',
            text=[f"{v:+.2f}%" for v in gdp_qoq],
            textposition='auto',
        ))
        fig.add_trace(go.Bar(
            x=gdp_countries,
            y=gdp_yoy,
            name='YoY',
            marker_color='#2196F3',
            text=[f"{v:+.2f}%" for v in gdp_yoy],
            textposition='auto',
        ))
        
        fig.update_layout(
            barmode='group',
            yaxis_title="Variation (%)",
            plot_bgcolor='#0A1929',
            paper_bgcolor='#0A1929',
            font=dict(color='white'),
            height=400,
            xaxis=dict(gridcolor='#1e3a5f'),
            yaxis=dict(gridcolor='#1e3a5f'),
            legend=dict(font=dict(color='white'))
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### CPI Variations")
        
        # Préparer les données pour le graphique
        cpi_countries = list(cpi_variations.keys())
        cpi_mom = [cpi_variations[c]['MoM'] for c in cpi_countries]
        cpi_yoy = [cpi_variations[c]['YoY'] for c in cpi_countries]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=cpi_countries,
            y=cpi_mom,
            name='MoM',
            marker_color="#FFB36B",
            text=[f"{v:+.2f}%" for v in cpi_mom],
            textposition='auto',
        ))
        fig.add_trace(go.Bar(
            x=cpi_countries,
            y=cpi_yoy,
            name='YoY',
            marker_color='#EE5A6F',
            text=[f"{v:+.2f}%" for v in cpi_yoy],
            textposition='auto',
        ))
        
        fig.update_layout(
            barmode='group',
            yaxis_title="Variation (%)",
            plot_bgcolor='#0A1929',
            paper_bgcolor='#0A1929',
            font=dict(color='white'),
            height=400,
            xaxis=dict(gridcolor='#1e3a5f'),
            yaxis=dict(gridcolor='#1e3a5f'),
            legend=dict(font=dict(color='white'))
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    st.markdown("### 👷 Unemployment Rate")

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            label="🇺🇸 USA Unemployment Rate",
            value=f"{unemp_summary['USA']['value']}%",
            delta=f"{unemp_summary['USA']['variation']}%"
            )
    with col2:
        st.metric(
            label="🇪🇺 Europe Unemployment Rate",
            value=f"{unemp_summary['Europe']['value']}%",
            delta=f"{unemp_summary['Europe']['variation']}%"
            )
    st.markdown("---")
    st.markdown("### 📉 Unemployment Rate – Historic")

    fig = go.Figure()
    colors = {'USA': '#FF6B6B', 'Europe': '#4FC3F7'}

    for region, series in unemp_data.items():
        fig.add_trace(go.Scatter(
            x=series.index,
            y=series.values,
            name=region,
            line=dict(color=colors[region], width=3),
            mode='lines'))
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Unemployment Rate (%)",
        hovermode='x unified',
        plot_bgcolor='#0A1929',
        paper_bgcolor='#0A1929',
        font=dict(color='white'),
        height=450,
        xaxis=dict(gridcolor='#1e3a5f'),
        yaxis=dict(gridcolor='#1e3a5f'),
    legend=dict(font=dict(color='white')))

    st.plotly_chart(fig, use_container_width=True)
    st.markdown("---")

    
    # Line chart GDP normalisé
    st.markdown("### Normalized GDP (Base 100)")
    st.markdown("""
    <div class='info-box'>
        <p><strong>💡 Graphic reading :</strong> This chart normalizes the GDP of each country to 100 at the start to facilitate comparison of growth trajectories. An upward line indicates faster growth.</p>
    </div>
    """, unsafe_allow_html=True)
    
    fig = go.Figure()
    colors = ['#4FC3F7', '#2196F3', '#1976D2', '#0D47A1', '#FF6B6B', '#EE5A6F']
    
    for i, (country, data) in enumerate(gdp_data.items()):
        normalized = (data / data.iloc[0]) * 100
        fig.add_trace(go.Scatter(
            x=normalized.index,
            y=normalized.values,
            name=country,
            line=dict(color=colors[i % len(colors)], width=3),
            mode='lines'
        ))
    
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Normalized GDP (Base 100)",
        hovermode='x unified',
        plot_bgcolor='#0A1929',
        paper_bgcolor='#0A1929',
        font=dict(color='white'),
        height=500,
        xaxis=dict(gridcolor='#1e3a5f'),
        yaxis=dict(gridcolor='#1e3a5f'),
        legend=dict(font=dict(color='white'))
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("""
    <div class='info-box'>
        <p>📌 <strong>Note :</strong> GDP updated quarterly | CPI updated monthly</p>
    </div>
    """, unsafe_allow_html=True)

# ========== PAGE FOREX & COMMODITIES ==========
elif st.session_state.page == 'forex_commodities':
    col1, col2 = st.columns([6, 1])
    with col1:
        st.markdown("## Forex & Commodities")
    with col2:
        if st.button("Retour", use_container_width=True):
            st.session_state.page = 'home'
            st.rerun()
    
    st.markdown("""
    <div class='info-box'>
        <p><strong>💡 How to interpret these data :</strong></p>
        <p>• <strong>Forex</strong> : Exchange rates between currencies. An increase in EURUSD means the euro strengthens against the dollar.</p>
        <p>• <strong>Gold</strong> : Safe-haven asset during uncertainty. Rises generally when markets are volatile.</p>
        <p>• <strong>Oil</strong> : Indicator of global economic activity. A rise can signal strong demand or geopolitical tensions.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("#### 🌍 Selection of countries for Forex")
    forex_countries = st.multiselect(
    "Choose countries for Forex",
    ['USA', 'France', 'Germany', 'UK', 'China', 'Japan'],
    default=['USA', 'France', 'Germany']
)
    
    # 1. FOREX
    st.markdown("### Exchange Rate")
    
    # Déterminer les paires forex nécessaires
    forex_pairs = get_required_forex_pairs(forex_countries)
    
    if forex_pairs:
        forex_data, forex_summary = get_forex_data(forex_pairs, selected_period)
        
        # Cards de devises
        cols = st.columns(len(forex_pairs))
        for i, pair in enumerate(forex_pairs):
            if pair in forex_summary:
                data = forex_summary[pair]
                with cols[i]:
                    # Couleur selon variation
                    delta_color = "normal" if data['var_1m'] >= 0 else "inverse"
                    
                    st.metric(
                        label=pair,
                        value=f"{data['value']:.4f}",
                        delta=f"1M: {data['var_1m']:+.2f}%",
                        delta_color=delta_color
                    )
                    st.markdown(f"<p style='text-align: center; color: #B0BEC5; font-size: 0.85em;'>1W: {data['var_1w']:+.2f}%</p>", unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Line chart évolution
        st.markdown("#### Exchange Rate Evolution")
        
        fig = go.Figure()
        colors = ['#4FC3F7', '#2196F3', '#1976D2', '#0D47A1', '#FF6B6B']
        
        for i, (pair, data) in enumerate(forex_data.items()):
            fig.add_trace(go.Scatter(
                x=data.index,
                y=data.values,
                name=pair,
                line=dict(color=colors[i % len(colors)], width=3),
                mode='lines'
            ))
        
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Exchange Rate",
            hovermode='x unified',
            plot_bgcolor='#0A1929',
            paper_bgcolor='#0A1929',
            font=dict(color='white'),
            height=450,
            xaxis=dict(gridcolor='#1e3a5f'),
            yaxis=dict(gridcolor='#1e3a5f'),
            legend=dict(font=dict(color='white'))
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Select countries in the sidebar to display exchange rates")
    
    st.markdown("---")
    
    # 2. COMMODITIES
    st.markdown("### 🏆 Commodities")
    
    commodities = get_commodities_data(selected_period)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Gold")
        
        gold = commodities['Gold']
        gold_var = gold.pct_change().iloc[-1] * 100
        
        st.metric(
            "Gold Price",
            f"${gold.iloc[-1]:,.2f}",
            f"{gold_var:+.2f}%"
        )
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=gold.index,
            y=gold.values,
            fill='tozeroy',
            line=dict(color='#FFD700', width=3),
            fillcolor='rgba(255, 215, 0, 0.3)',
            name='Gold'
        ))
        
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Price (USD)",
            plot_bgcolor='#0A1929',
            paper_bgcolor='#0A1929',
            font=dict(color='white'),
            height=400,
            xaxis=dict(gridcolor='#1e3a5f'),
            yaxis=dict(gridcolor='#1e3a5f'),
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### Oil (WTI)")
        
        oil = commodities['Oil']
        oil_var = oil.pct_change().iloc[-1] * 100
        
        st.metric(
            "Oil Price",
            f"${oil.iloc[-1]:,.2f}",
            f"{oil_var:+.2f}%"
        )
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=oil.index,
            y=oil.values,
            fill='tozeroy',
            line=dict(color='#2196F3', width=3),
            fillcolor='rgba(33, 150, 243, 0.3)',
            name='Oil'
        ))
        
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Price (USD)",
            plot_bgcolor='#0A1929',
            paper_bgcolor='#0A1929',
            font=dict(color='white'),
            height=400,
            xaxis=dict(gridcolor='#1e3a5f'),
            yaxis=dict(gridcolor='#1e3a5f'),
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)

# ========== PAGE TAUX & OBLIGATIONS ==========
elif st.session_state.page == 'rates_bonds':
    col1, col2 = st.columns([6, 1])
    with col1:
        st.markdown("## Rates & Bonds")
    with col2:
        if st.button("Back", use_container_width=True):
            st.session_state.page = 'home'
            st.rerun()
    
    st.markdown("""
    <div class='info-box'>
        <p><strong>💡 How to interpret these data :</strong></p>
        <p>• <strong>Interest rates</strong> : Set by central banks to control inflation. An increase makes credit more expensive and slows the economy.</p>
        <p>• <strong>Bonds 10Y</strong> : Yield of government bonds. A high yield indicates more perceived risk or inflation expectations.</p>
        <p>• <strong>Spreads</strong> : Difference in interest rates between countries. A high spread indicates higher relative risk.</p>
        <p>• <strong>Yield Curve</strong> : Curve of returns based on maturity. An inverted curve (short-term > long-term) may signal a recession.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 1. TAUX DIRECTEURS
    st.markdown("### Interest Rates")
    
    rates = get_interest_rates()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🇺🇸 Effective Federal Funds Rate (FED)")
        
        fed_rate = rates['US_Fed']
        
        st.metric(
            "Current Rate",
            f"{fed_rate.iloc[-1]:.2f}%",
            f"{fed_rate.pct_change().iloc[-1]:+.2f}%"
        )
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=fed_rate.index,
            y=fed_rate.values,
            fill='tozeroy',
            line=dict(color='#4FC3F7', width=3),
            fillcolor='rgba(79, 195, 247, 0.3)',
            name='FED Rate'
        ))
        
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Rate (%)",
            plot_bgcolor='#0A1929',
            paper_bgcolor='#0A1929',
            font=dict(color='white'),
            height=400,
            xaxis=dict(gridcolor='#1e3a5f'),
            yaxis=dict(gridcolor='#1e3a5f'),
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### 🇪🇺 Euro Short-Term Rate (BCE)")
        
        ecb_rate = rates['Euro_ECB']
        
        st.metric(
            "Current Rate",
            f"{ecb_rate.iloc[-1]:.2f}%",
            f"{ecb_rate.pct_change().iloc[-1]:+.2f}%"
        )
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=ecb_rate.index,
            y=ecb_rate.values,
            fill='tozeroy',
            line=dict(color='#2196F3', width=3),
            fillcolor='rgba(33, 150, 243, 0.3)',
            name='ECB Rate'
        ))
        
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Rate (%)",
            plot_bgcolor='#0A1929',
            paper_bgcolor='#0A1929',
            font=dict(color='white'),
            height=400,
            xaxis=dict(gridcolor='#1e3a5f'),
            yaxis=dict(gridcolor='#1e3a5f'),
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # 2. OBLIGATIONS SOUVERAINES
    st.markdown("### Government Bonds 10 Years")
    
    # Filtrer les pays pour les obligations
    st.markdown("#### 🌍 SSelection of countries for bonds")
    bond_countries = st.multiselect(
    "Choose countries",
    ['USA', 'Germany', 'France', 'UK', 'Japan'],
    default=['USA', 'Germany', 'France'])
    
    if bond_countries:
        bond_data, bond_summary = get_bond_rates(bond_countries)
        
        # Cards des taux
        cols = st.columns(len(bond_countries))
        for i, country in enumerate(bond_countries):
            if country in bond_summary:
                data = bond_summary[country]
                with cols[i]:
                    delta_color = "normal" if data['variation'] >= 0 else "inverse"
                    
                    flag_emoji = {
                        'USA': '🇺🇸',
                        'Germany': '🇩🇪',
                        'France': '🇫🇷',
                        'UK': '🇬🇧',
                        'Japan': '🇯🇵'
                    }
                    
                    st.metric(
                        label=f"{flag_emoji.get(country, '')} {country} 10Y",
                        value=f"{data['value']:.2f}%",
                        delta=f"{data['variation']:+.2f}%",
                        delta_color=delta_color
                    )
        
        st.markdown("---")
        
        # Yield Curve (USA par défaut)
        st.markdown("#### Yield Curve (USA)")
        
        yield_curve_data = get_yield_curve('USA')
        
        if yield_curve_data:
            maturities = list(yield_curve_data.keys())
            rates_values = list(yield_curve_data.values())
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=maturities,
                y=rates_values,
                mode='lines+markers',
                line=dict(color='#4FC3F7', width=4),
                marker=dict(size=10, color='#2196F3'),
                fill='tozeroy',
                fillcolor='rgba(79, 195, 247, 0.2)'
            ))
            
            fig.update_layout(
                xaxis_title="Maturity",
                yaxis_title="Yield (%)",
                plot_bgcolor='#0A1929',
                paper_bgcolor='#0A1929',
                font=dict(color='white'),
                height=450,
                xaxis=dict(gridcolor='#1e3a5f'),
                yaxis=dict(gridcolor='#1e3a5f'),
                legend=dict(font=dict(color='white'))
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Graphique comparatif des obligations
        st.markdown("#### Comparison of 10Y Rates")
        
        fig = go.Figure()
        colors = ['#4FC3F7', '#2196F3', '#1976D2', '#0D47A1', '#FF6B6B']
        
        for i, (country, data) in enumerate(bond_data.items()):
            fig.add_trace(go.Scatter(
                x=data.index,
                y=data.values,
                name=f"{country} 10Y",
                line=dict(color=colors[i % len(colors)], width=3),
                mode='lines'
            ))
        
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Yield (%)",
            hovermode='x unified',
            plot_bgcolor='#0A1929',
            paper_bgcolor='#0A1929',
            font=dict(color='white'),
            height=500,
            xaxis=dict(gridcolor='#1e3a5f'),
            yaxis=dict(gridcolor='#1e3a5f'),
            legend=dict(font=dict(color='white'))
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Sélecteur de spreads
        st.markdown("#### Analysis of Spreads")
        
        if len(bond_summary) >= 2:
            col1, col2 = st.columns(2)
            
            with col1:
                country1 = st.selectbox("Country 1", list(bond_summary.keys()), index=0)
            
            with col2:
                other_countries = [c for c in bond_summary.keys() if c != country1]
                country2 = st.selectbox("Country 2", other_countries, index=0 if other_countries else None)
            
            if country1 and country2:
                spread = bond_summary[country2]['value'] - bond_summary[country1]['value']
                
                spread_color = "🟢" if spread > 0 else "🔴"
                
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, #1e3a5f 0%, #2a5298 100%); 
                            padding: 25px; border-radius: 15px; text-align: center; 
                            border-left: 5px solid #4FC3F7; margin: 20px 0;'>
                    <h3 style='color: white; margin-bottom: 10px;'>Spread {country2} - {country1}</h3>
                    <h1 style='color: #4FC3F7; margin: 0;'>{spread_color} {spread:+.2f} bps</h1>
                    <p style='color: #B0BEC5; margin-top: 10px; font-size: 0.9em;'>
                        The rate {country2} is {'higher' if spread > 0 else 'lower'} than the rate {country1}
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # Graphique du spread dans le temps
                if country1 in bond_data and country2 in bond_data:
                    spread_series = bond_data[country2] - bond_data[country1]
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=spread_series.index,
                        y=spread_series.values,
                        fill='tozeroy',
                        line=dict(color='#FF6B6B', width=3),
                        fillcolor='rgba(255, 107, 107, 0.3)',
                        name=f'Spread {country2}-{country1}'
                    ))
                    
                    fig.add_hline(y=0, line_dash="dash", line_color="white", line_width=2)
                    
                    fig.update_layout(
                        xaxis_title="Date",
                        yaxis_title="Spread (bps)",
                        plot_bgcolor='#0A1929',
                        paper_bgcolor='#0A1929',
                        font=dict(color='white'),
                        height=400,
                        xaxis=dict(gridcolor='#1e3a5f'),
                        yaxis=dict(gridcolor='#1e3a5f'),
                        showlegend=False
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Select countries in the sidebar to display bond rates")
    
    st.markdown("""
    <div class='info-box'>
        <p>📌 <strong>Note :</strong> The sovereign rates data is updated monthly</p>
    </div>
    """, unsafe_allow_html=True)

# ========== PAGE EQUITY ANALYSIS SUITE ==========
elif st.session_state.page == 'equity_suite':

    col1, col2 = st.columns([6, 1])
    with col1:
        st.markdown("## Equity Analysis Toolkit")
    with col2:
        if st.button("Back", use_container_width=True):
            st.session_state.page = 'home'
            st.rerun()

    st.markdown("""
    <div class='info-box'>
        <p>
        Complete equity analysis: price evolution, correlations
        and financial statements. Select a ticker to begin.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs([
        "Price & Chart",
        "Correlation Heatmap",
        "Financial Statements"
    ])

    # =====================================================
    # 1) PRICE & CHART
    # =====================================================
    with tab1:
        st.markdown("### Price & Chart")

        ticker = st.text_input(
            "Ticker (ex: AAPL, MSFT, NVDA)",
            value="",
            key="price_ticker"
        ).upper().strip()

        if ticker == "":
            st.info("Enter a ticker to display the price analysis.")
        else:
            try:
                tk = yf.Ticker(ticker)
                hist = clean_index(tk.history(period=selected_period))

                if hist.empty:
                    st.warning("Ticker invalid or data unavailable.")
                else:
                    colA, colB = st.columns(2)

                    last_price = hist["Close"].iloc[-1]
                    perf = (last_price / hist["Close"].iloc[0] - 1) * 100

                    with colA:
                        st.metric("Last Price", f"{last_price:.2f}")
                    with colB:
                        st.metric(f"Performance over {selected_period_label}", f"{perf:+.2f}%")

                    fig = px.line(
                        hist,
                        y="Close",
                        title=f"{ticker} Performance over {selected_period_label}"
                    )

                    fig.update_layout(
                        plot_bgcolor="#0A1929",
                        paper_bgcolor="#0A1929",
                        font=dict(color="white"),
                        height=450,
                        xaxis=dict(gridcolor="#1e3a5f"),
                        yaxis=dict(gridcolor="#1e3a5f")
                    )

                    st.plotly_chart(fig, use_container_width=True)

                    st.markdown("#### Last observations")
                    
                    st.markdown(
                        "<div class='dataframe-container'>"
                        + hist.tail(5)[["Open", "High", "Low", "Close", "Volume"]].to_html(classes='table table-striped', border=0)
                        + "</div>", unsafe_allow_html=True)
                
                    info = tk.info
                    st.markdown("#### Key Information")

                    col1, col2 = st.columns(2)

                    with col1:

                        with st.expander("Business & Identity", expanded=True):
                            st.write(f"**Sector:** {info.get('sector', 'N/A')}")
                            st.write(f"**Industry:** {info.get('industry', 'N/A')}")
                            st.write(f"**Currency:** {info.get('currency', 'N/A')}")
                            st.write(info.get("longBusinessSummary", "N/A"))

                        with st.expander("Valuation"):
                            st.metric("Trailing P/E", info.get("trailingPE", "N/A"))
                            st.metric("Forward P/E", info.get("forwardPE", "N/A"))
                            st.metric("Price to Book", info.get("priceToBook", "N/A"))
                            st.metric("Price to Sales (TTM)", info.get("priceToSalesTrailing12Months", "N/A"))
                            st.metric("Enterprise Value", format_number(info.get("enterpriseValue", "N/A")))  # <--- à formatter
                            st.metric("EV / Revenue", info.get("enterpriseToRevenue", "N/A"))
                            st.metric("EV / EBITDA", info.get("enterpriseToEbitda", "N/A"))
                            st.metric("PEG Ratio", info.get("trailingPegRatio", "N/A"))

                        with st.expander("Growth"):
                            st.metric("Revenue Growth", info.get("revenueGrowth", "N/A"))
                            st.metric("Earnings Growth", info.get("earningsGrowth", "N/A"))
                            st.metric("Earnings QoQ Growth", info.get("earningsQuarterlyGrowth", "N/A"))

                    with col2:

                        with st.expander("Profitability ratios"):
                            st.metric("Gross Margin", info.get("grossMargins", "N/A"))
                            st.metric("Operating Margin", info.get("operatingMargins", "N/A"))
                            st.metric("EBITDA Margin", info.get("ebitdaMargins", "N/A"))
                            st.metric("ROE", info.get("returnOnEquity", "N/A"))
                            st.metric("ROA", info.get("returnOnAssets", "N/A"))
                            st.metric("Profit Margin", info.get("profitMargins", "N/A"))

                        with st.expander("Cash Flow & Balance Sheet"):
                            st.metric("Total Revenue", format_number(info.get("totalRevenue", "N/A")))  # <--- à formatter
                            st.metric("EBITDA", format_number(info.get("ebitda", "N/A")))  # <--- à formatter
                            st.metric("Free Cash Flow", format_number(info.get("freeCashflow", "N/A")))  # <--- à formatter
                            st.metric("Operating Cash Flow", format_number(info.get("operatingCashflow", "N/A")))  # <--- à formatter
                            st.metric("Total Debt", format_number(info.get("totalDebt", "N/A")))  # <--- à formatter
                            st.metric("Total Cash", format_number(info.get("totalCash", "N/A")))  # <--- à formatter
                            st.metric("Debt to Equity", info.get("debtToEquity", "N/A"))
                            st.metric("Current Ratio", info.get("currentRatio", "N/A"))
                            st.metric("Quick Ratio", info.get("quickRatio", "N/A"))

                        with st.expander("Market Sentiment"):
                            st.metric("Target Low", format_number(info.get("targetLowPrice", "N/A")))  # <--- à formatter
                            st.metric("Target Mean", format_number(info.get("targetMeanPrice", "N/A")))  # <--- à formatter
                            st.metric("Target High", format_number(info.get("targetHighPrice", "N/A")))  # <--- à formatter
                            st.write(f"**Recommendation:** {info.get('recommendationKey', 'N/A')}")
                            st.metric("Recommendation Mean", info.get("recommendationMean", "N/A"))
                            st.metric("# Analysts", info.get("numberOfAnalystOpinions", "N/A"))

                        with st.expander("Governance & Risk"):
                            st.metric("Overall Risk", info.get("overallRisk", "N/A"))
                            st.metric("Audit Risk", info.get("auditRisk", "N/A"))
                            st.metric("Board Risk", info.get("boardRisk", "N/A"))
                            st.metric("Compensation Risk", info.get("compensationRisk", "N/A"))
                            st.metric("Shareholder Rights Risk", info.get("shareHolderRightsRisk", "N/A"))
            except Exception:
                st.error("Error loading ticker data.")

    # =====================================================
    # 2) CORRELATION HEATMAP
    # =====================================================
    with tab2:
        st.markdown("### Correlation Heatmap")

        st.markdown("""
        <div class='info-box'>
            <p>
            Analysis of correlations between several assets over 1 year.
            Enter at least two tickers separated by commas.
            </p>
        </div>
        """, unsafe_allow_html=True)

        tickers_input = st.text_input(
            "Tickers (ex: AAPL,MSFT,NVDA)",
            value="",
            key="corr_tickers"
        ).upper().strip()

        if tickers_input == "":
            st.info("Entrez des tickers pour afficher la matrice de corrélation.")
        else:
            tickers = [t.strip() for t in tickers_input.split(",") if t.strip()]

            if len(tickers) < 2:
                st.warning("Veuillez entrer au moins deux tickers.")
            else:
                df = pd.DataFrame()

                for t in tickers:
                    data = yf.Ticker(t).history(period=selected_period)["Close"]
                    if not data.empty:
                        df[t] = data

                if df.shape[1] < 2:
                    st.warning("Données insuffisantes pour calculer la corrélation.")
                else:
                    corr = df.corr()

                    fig = px.imshow(
                        corr,
                        text_auto=True,
                        color_continuous_scale="Blues"
                    )

                    fig.update_layout(
                        plot_bgcolor="#0A1929",
                        paper_bgcolor="#0A1929",
                        font=dict(color="white"),
                        height=500
                    )

                    st.plotly_chart(fig, use_container_width=True)

                    st.download_button(
                        "Télécharger CSV",
                        corr.to_csv().encode(),
                        "correlations.csv"
                    )

    # =====================================================
    # 3) FINANCIAL STATEMENTS
    # =====================================================
    with tab3:
        st.markdown("### Financial Statements")

        ticker_fs = st.text_input(
            "Ticker (ex: AAPL)",
            value="",
            key="fs_ticker"
        ).upper().strip()

        choice = st.selectbox(
            "Type d'état financier",
            ["Income Statement", "Balance Sheet", "Cash Flow Statement"]
        )
        
        def format_number(x):
            """Formate les nombres pour les rendre lisibles."""
            if pd.isna(x):
                return "N/A"
            elif abs(x) >= 1_000_000_000:
                return f"{x/1_000_000_000:.2f} B"
            elif abs(x) >= 1_000_000:
                return f"{x/1_000_000:.2f} M"
            elif abs(x) >= 1_000:
                return f"{x/1_000:.2f} K"
            else:
                return f"{x:.2f}"

        def format_fs_numbers(df):
            """Formate toutes les valeurs numériques d'un DataFrame financier."""
            df_formatted = df.copy()
            for col in df_formatted.columns:
                df_formatted[col] = df_formatted[col].apply(format_number)
            return df_formatted

        # Injecte le CSS pour styliser le tableau HTML
        st.markdown("""
        <style>
        .dataframe-container table {
            background-color: #0A1929 !important;
            color: white !important;
            border-collapse: collapse;
            width: 100%;
        }
        .dataframe-container th, .dataframe-container td {
            border: 3px solid white !important;
            padding: 5px;
            text-align: right;
        }
        .dataframe-container th {
            background-color: #0A1929 !important;
            font-weight: bold;
        }
        </style>
        """, unsafe_allow_html=True)

        if ticker_fs == "":
            st.info("Entrez un ticker pour afficher les états financiers.")
        else:
            try:
                tk = yf.Ticker(ticker_fs)

                if choice == "Income Statement":
                    fs = tk.financials
                elif choice == "Balance Sheet":
                    fs = tk.balance_sheet
                else:
                    fs = tk.cashflow

                if fs is None or fs.empty:
                    st.warning("Données financières indisponibles.")
                else:
                    # Formater les nombres pour l'affichage
                    fs = clean_index(fs)
                    fs_formatted = format_fs_numbers(fs)
                    st.markdown("<div class='dataframe-container'>", unsafe_allow_html=True)
                    st.markdown(fs_formatted.to_html(), unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

                    # Bouton de téléchargement CSV
                    st.download_button(
                        "Télécharger CSV",
                        fs.to_csv().encode(),
                        f"{ticker_fs}_{choice}.csv"
                    )

            except Exception:
                st.error("Erreur lors du chargement des états financiers.")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #B0BEC5; padding: 20px;'>
    <p style='font-size: 1.1em;'><strong>Hirsch Capital</strong></p>
    <p style='font-size: 0.85em;'>Dashboard Macro Économique | Données: FRED & Yahoo Finance</p>
</div>
""", unsafe_allow_html=True)
