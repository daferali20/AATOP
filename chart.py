# chart.py
import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go

def fetch_tradingview_data(symbol, interval='D', count=100):
    """جلب بيانات السهم من TradingView"""
    url = f"https://www.tradingview.com/chart/?symbol={symbol}"
    # Note: تحتاج إلى استبدال هذا بمصدر بيانات حقيقي أو استخدام API مثل Twelve Data
    # هذا مثال افتراضي فقط
    data = {
        'date': pd.date_range(end=pd.Timestamp.today(), periods=count).tolist(),
        'close': [100 + i + (i % 7) for i in range(count)]  # بيانات افتراضية
    }
    return pd.DataFrame(data)

def plot_stock_chart(symbol, days=90):
    """إنشاء شارت تفاعلي باستخدام Plotly"""
    df = fetch_tradingview_data(symbol)
    df = df.tail(days)  # عرض آخر X يوم
    
    fig = go.Figure()
    
    # خط السعر
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['close'],
        name='السعر',
        line=dict(color='#3498db', width=2)
    ))
    
    # تخصيص الشكل
    fig.update_layout(
        title=f'{symbol} - أداء السهم',
        xaxis_title='التاريخ',
        yaxis_title='السعر (USD)',
        hovermode="x unified",
        template="plotly_white"
    )
    
    return fig
