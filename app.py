import streamlit as st
import requests
import pandas as pd
from dotenv import load_dotenv
import os
# عنوان التطبيق
st.set_page_config(page_title="الأسهم الأكثر تداولاً وارتفاعاً", layout="wide")
st.title("📈 الأسهم الأكثر تداولاً وارتفاعاً (1$ إلى 55$)")

# شريط جانبي للإعدادات
with st.sidebar:
    st.header("الإعدادات")
    min_price = st.number_input("الحد الأدنى للسعر ($)", min_value=0.0, value=1.0, step=0.5)
    max_price = st.number_input("الحد الأقصى للسعر ($)", min_value=0.0, value=55.0, step=0.5)
    api_key = st.text_input("مفتاح API (اختياري)", value="CVROqS2TTsTM06ZNpYQJd5C1dXg1Amuv", type="password")
    st.markdown("[احصل على مفتاح API مجاني](https://financialmodelingprep.com/developer/docs/)")

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
        
        df_active_filtered = df_active[(df_active['price'] >= min_price) & (df_active['price'] <= max_price)]
        df_gainers_filtered = df_gainers[(df_gainers['price'] >= min_price) & (df_gainers['price'] <= max_price)]
        
        return df_active_filtered, df_gainers_filtered
        
    except Exception as e:
        st.error(f"حدث خطأ: {e}")
        return pd.DataFrame(), pd.DataFrame()

# زر التحديث
if st.button("🔄 تحديث البيانات"):
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
