import streamlit as st
from dotenv import load_dotenv
import os
import requests
import pandas as pd
from datetime import datetime

# تحميل متغيرات البيئة
load_dotenv()

# إعداد الصفحة
st.set_page_config(
    page_title="الأسهم الأكثر تداولاً وارتفاعاً",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تحميل CSS مخصص
def load_custom_css():
    st.markdown("""
    <style>
        :root {
            --primary-color: #3498db;
            --secondary-color: #2980b9;
        }
        body { font-family: 'Arial', sans-serif; color: #333333; }
        h1 { color: #2c3e50; border-bottom: 2px solid var(--primary-color); padding-bottom: 10px; }
        .stDataFrame { border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .stButton>button {
            background-color: var(--primary-color); 
            color: white; 
            border-radius: 5px;
            padding: 8px 16px; 
            transition: all 0.3s;
        }
        .stButton>button:hover {
            background-color: var(--secondary-color); 
            transform: translateY(-1px);
        }
        .telegram-btn { background-color: #0088cc !important; margin: 10px 0; }
        .tradingview-widget-container {
            border: 1px solid #e0e0e0; 
            border-radius: 10px;
            padding: 10px; 
            margin-top: 20px;
        }
        .sidebar .sidebar-content {
            background-color: #f8f9fa;
        }
    </style>
    """, unsafe_allow_html=True)

load_custom_css()

# إدارة المفاتيح السرية
class Config:
    def __init__(self):
        self.API_KEY = os.getenv("API_KEY", "CVROqS2TTsTM06ZNpYQJd5C1dXg1Amuv")
        self.TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
        self.TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
        
        # التحقق من المفاتيح
        if not self.API_KEY:
            st.error("API_KEY غير موجود في ملف .env")
        if not self.TELEGRAM_TOKEN:
            st.warning("TELEGRAM_BOT_TOKEN غير موجود في ملف .env")
        if not self.TELEGRAM_CHAT_ID:
            st.warning("TELEGRAM_CHAT_ID غير موجود في ملف .env")

config = Config()

# وظائف مساعدة
def fetch_stock_data(api_key, symbol="AAPL"):
    """جلب بيانات الأسهم من API"""
    try:
        url = f"https://financialmodelingprep.com/api/v3/quote/{symbol}?apikey={api_key}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"خطأ في جلب البيانات: {e}")
        return None

def display_stock_data(data):
    """عرض بيانات الأسهم"""
    if not data:
        return
        
    df = pd.DataFrame(data)
    
    # إعادة تسمية الأعمدة للعرض بالعربية
    column_mapping = {
        'symbol': 'الرمز',
        'name': 'الاسم',
        'price': 'السعر',
        'change': 'التغيير',
        'changesPercentage': 'النسبة المئوية للتغيير',
        'volume': 'حجم التداول'
    }
    
    df = df.rename(columns=column_mapping)
    st.dataframe(df)

# الواجهة الرئيسية
def main():
    st.title("📈 لوحة تحليل الأسهم")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.header("الأسهم الأكثر نشاطاً")
        stock_data = fetch_stock_data(config.API_KEY)
        display_stock_data(stock_data)
        
    with col2:
        st.header("الإعدادات")
        symbol = st.text_input("أدخل رمز السهم", value="AAPL")
        
        if st.button("جلب البيانات", key="fetch_data"):
            with st.spinner("جاري جلب البيانات..."):
                data = fetch_stock_data(config.API_KEY, symbol)
                display_stock_data(data)
    
    # قسم الرسوم البيانية
    st.header("الرسوم البيانية المباشرة")
    st.markdown("""
    <div class="tradingview-widget-container">
        <!-- TradingView Widget سيتم إضافته هنا -->
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
