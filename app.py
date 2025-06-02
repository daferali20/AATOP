import streamlit as st
from dotenv import load_dotenv
import os
import requests
import pandas as pd
import streamlit.components.v1 as components
# تحميل المتغيرات من ملف .env
load_dotenv()

# عنوان التطبيق
st.set_page_config(page_title="الأسهم الأكثر تداولاً وارتفاعاً", layout="wide")
st.set_page_config(layout="wide")
st.title("📈 شارت الأسهم من TradingView")
# تحميل ملف CSS المخصص
def load_custom_css():
    css = """
    <style>
        /* تنسيق عام */
        body {
            font-family: 'Arial', sans-serif;
            color: #333333;
        }
        
        /* العناوين */
        h1 {
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }
        
        /* الجداول */
        .stDataFrame {
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        /* الأزرار */
        .stButton>button {
            background-color: #3498db;
            color: white;
            border-radius: 5px;
            padding: 8px 16px;
            transition: all 0.3s;
        }
        
        .stButton>button:hover {
            background-color: #2980b9;
            transform: translateY(-1px);
        }
        
        /* الشريط الجانبي */
        .css-1d391kg {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
        }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

load_custom_css()

st.title("📈 الأسهم الأكثر تداولاً وارتفاعاً (1$ إلى 55$)")

# استرجاع مفتاح API (مع الأولوية لما يدخله المستخدم)
default_api_key = os.getenv("API_KEY", "CVROqS2TTsTM06ZNpYQJd5C1dXg1Amuv")

# شريط جانبي للإعدادات
with st.sidebar:
    st.header("الإعدادات")
    min_price = st.number_input("الحد الأدنى للسعر ($)", min_value=0.0, value=1.0, step=0.5)
    max_price = st.number_input("الحد الأقصى للسعر ($)", min_value=0.0, value=55.0, step=0.5)
    user_api_key = st.text_input("مفتاح API (اختياري)", value=default_api_key, type="password")
    st.markdown("[احصل على مفتاح API مجاني](https://financialmodelingprep.com/developer/docs/)")

# استخدام المفتاح الذي أدخله المستخدم أو المفتاح الافتراضي
api_key = user_api_key if user_api_key else default_api_key

def get_stock_data(api_key, min_price, max_price):
    try:
        # جلب الأسهم الأكثر تداولاً
        active_url = f"https://financialmodelingprep.com/api/v3/stock_market/actives?apikey={api_key}"
        active_data = requests.get(active_url).json()
        
        # جلب الأسهم الأكثر ارتفاعاً
        gainers_url = f"https://financialmodelingprep.com/api/v3/stock_market/gainers?apikey={api_key}"
        gainers_data = requests.get(gainers_url).json()
        
        # تحويل إلى DataFrames وتصفية حسب السعر
        df_active = pd.DataFrame(active_data)
        df_gainers = pd.DataFrame(gainers_data)
        
        # تصفية حسب السعر (1$ إلى 55$)
        df_active_filtered = df_active[(df_active['price'] >= min_price) & (df_active['price'] <= max_price)]
        df_gainers_filtered = df_gainers[(df_gainers['price'] >= min_price) & (df_gainers['price'] <= max_price)]
        
        # 🔥🔥 **استبعاد الأسهم التي حدث لها تقسيم عكسي (Split)**:
        # الشرط: إذا كان "change" أو "changesPercentage" سالبًا، فهذا يعني انخفاض السهم (تقسيم عكسي)
        df_gainers_filtered = df_gainers_filtered[
            (df_gainers_filtered['change'] > 0) &  # التغير موجب (ارتفاع)
            (df_gainers_filtered['changesPercentage'] > 0)  # النسبة المئوية موجبة (ارتفاع)
        ]
        
        return df_active_filtered, df_gainers_filtered
        
    except Exception as e:
        st.error(f"حدث خطأ: {e}")
        return pd.DataFrame(), pd.DataFrame()
def render_tradingview_chart():
    with open("tradingview_chart.html", "r") as f:
        html_content = f.read()
        st.components.v1.html(html_content, height=550)



render_tradingview_chart()
# زر التحديث
if st.button("🔄 تحديث البيانات", key="refresh_button"):
    st.session_state['active'], st.session_state['gainers'] = get_stock_data(api_key, min_price, max_price)

# عرض البيانات إذا كانت موجودة
if 'active' in st.session_state:
    st.subheader("الأسهم الأكثر تداولاً")
    st.dataframe(
        st.session_state['active'][['symbol', 'name', 'price', 'change', 'changesPercentage']],
        column_config={
            "symbol": "الرمز",
            "name": "اسم السهم",
            "price": st.column_config.NumberColumn("السعر ($)", format="%.2f"),
            "change": st.column_config.NumberColumn("التغيير", format="%.2f"),
            "changesPercentage": st.column_config.NumberColumn("النسبة المئوية", format="%.2f%%")
        },
        hide_index=True,
        use_container_width=True
    )

if 'gainers' in st.session_state:
    st.subheader("الأسهم الأكثر ارتفاعاً")
    st.dataframe(
        st.session_state['gainers'][['symbol', 'name', 'price', 'change', 'changesPercentage']],
        column_config={
            "symbol": "الرمز",
            "name": "اسم السهم",
            "price": st.column_config.NumberColumn("السعر ($)", format="%.2f"),
            "change": st.column_config.NumberColumn("التغيير", format="%.2f"),
            "changesPercentage": st.column_config.NumberColumn("النسبة المئوية", format="%.2f%%")
        },
        hide_index=True,
        use_container_width=True
    )

