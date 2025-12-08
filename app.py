import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Page config
st.set_page_config(
    page_title="FAWN Weather Dashboard",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv('FAWN_Newreport_features.csv')
    if 'Period' in df.columns:
        df['Period'] = pd.to_datetime(df['Period'], errors='coerce')
    return df

df = load_data()

# Header
st.markdown('<div class="main-header">🌤️ FAWN Weather Dashboard</div>', unsafe_allow_html=True)
st.markdown("**Florida Automated Weather Network - Interactive Data Explorer**")
st.markdown("---")

# Sidebar - Filters
st.sidebar.header("🔍 Filter Options")

# Station filter
stations = ['All Stations'] + sorted(df['FAWN Station'].unique().tolist())
selected_station = st.sidebar.selectbox("Select Station", stations)

# Date range filter
if 'Period' in df.columns and df['Period'].notna().any():
    min_date = df['Period'].min().date()
    max_date = df['Period'].max().date()
    date_range = st.sidebar.date_input(
        "Select Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
else:
    date_range = None

# Season filter
if 'Season' in df.columns:
    seasons = ['All Seasons'] + sorted(df['Season'].dropna().unique().tolist())
    selected_season = st.sidebar.selectbox("Select Season", seasons)
else:
    selected_season = 'All Seasons'

# Temperature range filter
temp_range = st.sidebar.slider(
    "Temperature Range (°F)",
    float(df['2m T avg (F)'].min()),
    float(df['2m T avg (F)'].max()),
    (float(df['2m T avg (F)'].min()), float(df['2m T avg (F)'].max()))
)

# Apply filters
filtered_df = df.copy()

if selected_station != 'All Stations':
    filtered_df = filtered_df[filtered_df['FAWN Station'] == selected_station]

if date_range and len(date_range) == 2:
    filtered_df = filtered_df[
        (filtered_df['Period'].dt.date >= date_range[0]) &
        (filtered_df['Period'].dt.date <= date_range[1])
    ]

if selected_season != 'All Seasons' and 'Season' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['Season'] == selected_season]

filtered_df = filtered_df[
    (filtered_df['2m T avg (F)'] >= temp_range[0]) &
    (filtered_df['2m T avg (F)'] <= temp_range[1])
]

st.sidebar.markdown(f"**Records shown: {len(filtered_df):,} / {len(df):,}**")

# Main Dashboard
# Row 1: Key Metrics
st.header("📊 Key Metrics")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    avg_temp = filtered_df['2m T avg (F)'].mean()
    st.metric("Avg Temperature", f"{avg_temp:.1f}°F")

with col2:
    total_rain = filtered_df['2m Rain tot (in)'].sum()
    st.metric("Total Rainfall", f"{total_rain:.2f} in")

with col3:
    avg_humidity = filtered_df['RelHum avg 2m  (pct)'].mean()
    st.metric("Avg Humidity", f"{avg_humidity:.1f}%")

with col4:
    avg_wind = filtered_df['10m Wind avg (mph)'].mean()
    st.metric("Avg Wind Speed", f"{avg_wind:.1f} mph")

with col5:
    if 'Comfort_Index' in filtered_df.columns:
        avg_comfort = filtered_df['Comfort_Index'].mean()
        st.metric("Comfort Index", f"{avg_comfort:.1f}")
    else:
        st.metric("Stations", f"{filtered_df['FAWN Station'].nunique()}")

st.markdown("---")

# Row 2: Temperature Analysis
st.header("🌡️ Temperature Analysis")

tab1, tab2, tab3 = st.tabs(["Time Series", "Distribution", "By Station"])

with tab1:
    if 'Period' in filtered_df.columns:
        fig = px.line(
            filtered_df.sort_values('Period'),
            x='Period',
            y='2m T avg (F)',
            title='Temperature Over Time',
            labels={'2m T avg (F)': 'Temperature (°F)', 'Period': 'Date'}
        )
        fig.update_traces(line_color='#ff7f0e')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Period data not available")

with tab2:
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.histogram(
            filtered_df,
            x='2m T avg (F)',
            nbins=50,
            title='Temperature Distribution',
            labels={'2m T avg (F)': 'Temperature (°F)'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if 'Season' in filtered_df.columns:
            fig = px.box(
                filtered_df,
                x='Season',
                y='2m T avg (F)',
                title='Temperature by Season',
                labels={'2m T avg (F)': 'Temperature (°F)'},
                color='Season'
            )
            st.plotly_chart(fig, use_container_width=True)

with tab3:
    station_stats = filtered_df.groupby('FAWN Station').agg({
        '2m T avg (F)': ['mean', 'min', 'max', 'std']
    }).round(2)
    station_stats.columns = ['Mean', 'Min', 'Max', 'Std Dev']
    station_stats = station_stats.sort_values('Mean', ascending=False)
    
    fig = px.bar(
        station_stats.reset_index(),
        x='FAWN Station',
        y='Mean',
        title='Average Temperature by Station',
        labels={'Mean': 'Avg Temperature (°F)'}
    )
    st.plotly_chart(fig, use_container_width=True)
    
    with st.expander("View Station Statistics Table"):
        st.dataframe(station_stats, use_container_width=True)

st.markdown("---")

# Row 3: Weather Conditions
st.header("🌧️ Weather Conditions")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Precipitation Analysis")
    
    # Rain days
    rain_days = (filtered_df['2m Rain tot (in)'] > 0).sum()
    total_days = len(filtered_df)
    rain_pct = (rain_days / total_days * 100) if total_days > 0 else 0
    
    st.metric("Days with Rain", f"{rain_days} ({rain_pct:.1f}%)")
    
    # Rain intensity histogram
    rain_data = filtered_df[filtered_df['2m Rain tot (in)'] > 0]
    if len(rain_data) > 0:
        fig = px.histogram(
            rain_data,
            x='2m Rain tot (in)',
            nbins=30,
            title='Rainfall Distribution (Rain Days Only)',
            labels={'2m Rain tot (in)': 'Rainfall (inches)'}
        )
        fig.update_traces(marker_color='blue')
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Wind Analysis")
    
    avg_wind = filtered_df['10m Wind avg (mph)'].mean()
    max_wind = filtered_df['10m Wind max (mph)'].max()
    
    col_a, col_b = st.columns(2)
    col_a.metric("Avg Wind", f"{avg_wind:.1f} mph")
    col_b.metric("Max Wind", f"{max_wind:.1f} mph")
    
    # Wind speed distribution
    fig = px.histogram(
        filtered_df,
        x='10m Wind avg (mph)',
        nbins=30,
        title='Wind Speed Distribution',
        labels={'10m Wind avg (mph)': 'Wind Speed (mph)'}
    )
    fig.update_traces(marker_color='orange')
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# Row 4: Relationships
st.header("🔗 Weather Relationships")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Temperature vs Humidity")
    fig = px.scatter(
        filtered_df.sample(min(1000, len(filtered_df))),
        x='2m T avg (F)',
        y='RelHum avg 2m  (pct)',
        color='2m Rain tot (in)',
        title='Temperature vs Humidity (colored by rainfall)',
        labels={
            '2m T avg (F)': 'Temperature (°F)',
            'RelHum avg 2m  (pct)': 'Humidity (%)',
            '2m Rain tot (in)': 'Rain (in)'
        },
        opacity=0.6
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Temperature vs Wind Speed")
    fig = px.scatter(
        filtered_df.sample(min(1000, len(filtered_df))),
        x='2m T avg (F)',
        y='10m Wind avg (mph)',
        title='Temperature vs Wind Speed',
        labels={
            '2m T avg (F)': 'Temperature (°F)',
            '10m Wind avg (mph)': 'Wind Speed (mph)'
        },
        opacity=0.6
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# Row 5: Advanced Features
if 'Comfort_Index' in filtered_df.columns or 'Weather_Severity' in filtered_df.columns:
    st.header("📈 Engineered Features")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if 'Comfort_Index' in filtered_df.columns:
            fig = px.histogram(
                filtered_df,
                x='Comfort_Index',
                nbins=40,
                title='Comfort Index Distribution',
                labels={'Comfort_Index': 'Comfort Index (0-100)'}
            )
            fig.update_traces(marker_color='green')
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if 'Weather_Severity' in filtered_df.columns:
            fig = px.histogram(
                filtered_df,
                x='Weather_Severity',
                nbins=40,
                title='Weather Severity Index',
                labels={'Weather_Severity': 'Severity Score'}
            )
            fig.update_traces(marker_color='red')
            st.plotly_chart(fig, use_container_width=True)

# Data Explorer
st.markdown("---")
st.header("📋 Data Explorer")

if st.checkbox("Show Raw Data"):
    st.dataframe(filtered_df.head(100), use_container_width=True)
    
    # Download button
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        label="Download Filtered Data as CSV",
        data=csv,
        file_name=f"fawn_filtered_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>FAWN Weather Data Dashboard | Data Source: Florida Automated Weather Network</p>
    <p>Created for EDA Project | Last Updated: {}</p>
</div>
""".format(datetime.now().strftime('%Y-%m-%d %H:%M')), unsafe_allow_html=True)