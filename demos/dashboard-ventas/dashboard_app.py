import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
from datetime import datetime
import time

engine = create_engine('postgresql://usuario:contrasena@localhost:5432/sales_dashboard')

st.set_page_config(page_title="💄 Beauty Sales Dashboard", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
        :root {
            --primary: #D8BFD8;
            --secondary: #FFB6D9;
            --accent: #E6D5E8;
            --light: #FFF0F5;
        }

        .main-title {
            font-size: 3em;
            font-weight: 700;
            background: linear-gradient(135deg, #FF69B4 0%, #FF1493 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-align: center;
            margin-bottom: 10px;
        }

        .subtitle {
            text-align: center;
            color: #C25A7B;
            font-size: 1.1em;
            font-weight: 500;
            margin-bottom: 30px;
        }

        .metric-card {
            background: linear-gradient(135deg, #FFE4F0 0%, #F0E4FF 100%);
            padding: 25px;
            border-radius: 15px;
            border: 2px solid #FFB6D9;
            box-shadow: 0 8px 20px rgba(216, 165, 255, 0.15);
            text-align: center;
        }

        .metric-value {
            font-size: 2.5em;
            font-weight: 800;
            background: linear-gradient(135deg, #FF69B4 0%, #FF1493 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .metric-label {
            font-size: 1em;
            color: #C25A7B;
            font-weight: 600;
            margin-top: 10px;
        }

        .stButton > button {
            background: linear-gradient(135deg, #FF69B4 0%, #FF1493 100%);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 25px;
            font-weight: 600;
            font-size: 1em;
            box-shadow: 0 4px 15px rgba(255, 105, 180, 0.3);
            transition: all 0.3s ease;
        }

        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(255, 105, 180, 0.4);
        }

        .subheader-modern {
            font-size: 1.8em;
            font-weight: 700;
            color: #C25A7B;
            margin-top: 40px;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #FF69B4;
        }

        .refresh-info {
            text-align: center;
            color: #FF69B4;
            font-size: 0.95em;
            font-weight: 500;
            margin-top: 10px;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">💄 Beauty Sales Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Cosmetics & Beauty Products Analytics</div>', unsafe_allow_html=True)

if 'last_refresh' not in st.session_state:
    st.session_state['last_refresh'] = datetime.now()

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button(" Refresh Now", use_container_width=True):
        st.session_state['last_refresh'] = datetime.now()

st.markdown(f'<div class="refresh-info">Last updated: {st.session_state["last_refresh"].strftime("%H:%M:%S")}</div>', unsafe_allow_html=True)


@st.cache_data(ttl=60)
def load_data():
    query = "SELECT * FROM sales_data ORDER BY sale_time DESC LIMIT 100;"
    df = pd.read_sql(query, engine)
    return df

df = load_data()

st.markdown('<div class="subheader-modern"> Key Metrics</div>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_sales = df['total_sales'].sum()
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">${total_sales:,.0f}</div>
            <div class="metric-label">Revenue</div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    avg_sales = df['total_sales'].mean()
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">${avg_sales:,.0f}</div>
            <div class="metric-label"> Avg Sale</div>
        </div>
    """, unsafe_allow_html=True)

with col3:
    num_transactions = len(df)
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{num_transactions}</div>
            <div class="metric-label"> Orders</div>
        </div>
    """, unsafe_allow_html=True)

with col4:
    num_regions = df['region'].nunique()
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{num_regions}</div>
            <div class="metric-label"> Cities</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown('<div class="subheader-modern"> Latest Orders</div>', unsafe_allow_html=True)
st.dataframe(df, use_container_width=True, hide_index=True)

st.markdown('<div class="subheader-modern">💄 Beauty Products Performance</div>', unsafe_allow_html=True)

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.markdown('<div style="text-align: center; margin-bottom: 20px;"><h3 style="color: #C25A7B;"> Sales by Product</h3></div>', unsafe_allow_html=True)
    fig = px.bar(
        df,
        x='product',
        y='total_sales',
        color='region',
        color_discrete_sequence=['#FFB6D9', '#FF69B4', '#FF1493', '#C25A7B', '#FFE4F0'],
        title="",
        labels={'total_sales': 'Sales ($)', 'product': 'Product', 'region': 'City'}
    )
    fig.update_layout(
        plot_bgcolor='#FFF0F5',
        paper_bgcolor='#FFFFFF',
        font=dict(family="Arial, sans-serif", color="#C25A7B", size=12),
        hovermode='x unified',
        margin=dict(l=0, r=0, t=0, b=0)
    )
    fig.update_traces(marker=dict(opacity=0.8, line=dict(width=1, color='white')))
    st.plotly_chart(fig, use_container_width=True)

with chart_col2:
    st.markdown('<div style="text-align: center; margin-bottom: 20px;"><h3 style="color: #C25A7B;"> Sales by City</h3></div>', unsafe_allow_html=True)
    region_data = df.groupby("region")["total_sales"].sum().reset_index()
    fig2 = px.pie(
        region_data,
        values="total_sales",
        names="region",
        color_discrete_sequence=['#FFB6D9', '#FF69B4', '#FF1493', '#C25A7B', '#FFE4F0', '#D8BFD8'],
        title=""
    )
    fig2.update_layout(
        paper_bgcolor='#FFFFFF',
        font=dict(family="Arial, sans-serif", color="#C25A7B", size=12),
        margin=dict(l=0, r=0, t=0, b=0)
    )
    fig2.update_traces(textposition='inside', textinfo='percent+label', marker=dict(line=dict(color='white', width=2)))
    st.plotly_chart(fig2, use_container_width=True)


time.sleep(60)
st.rerun()
