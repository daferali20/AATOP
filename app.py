import streamlit as st
from dotenv import load_dotenv
import os
import requests
import pandas as pd
import streamlit.components.v1 as components
from datetime import datetime, date, time as dt_time
from streamlit_autorefresh import st_autorefresh

# تحميل متغيرات البيئة
load_dotenv()

# إعداد الصفحة
st.set_page_config(page_title="الأسهم الأكثر تداولاً وارتفاعاً", layout="wide")

# تحميل CSS مخصص
def load_custom_css():
    css = """
    <style>
        body { font-family: 'Arial', sans-serif; color: #333333; }
        h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
        .stDataFrame { border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .stButton>button {
            background-color: #3498db; color: white; border-radius: 5px;
            padding: 8px 16px; transition: all 0.3s;
        }
        .stButton>button:hover {
            background-color: #2980b9; transform: translateY(-1px);
        }
        .telegram-btn { background-color: #0088cc !important; margin: 10px 0; }
        .tradingview-chart {
            border: 1px solid #e0e0e0; border-radius: 10px;
            padding: 10px; margin-top: 20px;
        }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

load_custom_css()

# الثوابت
DEFAULT_API_KEY = os.getenv("API_KEY", "CVROqS2TTsTM06ZNpYQJd5C1dXg1Amuv")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# دالة تنسيق رمز السهم لـ TradingView
def format_symbol_for_tradingview(symbol):
    return f"NASDAQ:{symbol}"

# دالة عرض شارت TradingView
def show_tradingview_chart(symbol):
    tv_symbol = format_symbol_for_tradingview(symbol)
    html_code = f"""
    <div class="tradingview-widget-container">
      <div id="tradingview_{symbol}" style="height: 500px;"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
        new TradingView.widget({{
            "autosize": true,
            "symbol": "{tv_symbol}",
            "interval": "D",
            "timezone": "Etc/UTC",
            "theme": "light",
            "style": "1",
            "locale": "ar",
            "toolbar_bg": "#f1f3f6",
            "enable_publishing": false,
            "container_id": "tradingview_{symbol}"
        }});
      </script>
    </div>
    """
    st.markdown("<div class='tradingview-chart'>", unsafe_allow_html=True)
    components.html(html_code, height=550)
    st.markdown("</div>", unsafe_allow_html=True)

# دالة إرسال تلغرام
def send_telegram_message(message):
    if not message:
        return False
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        try:
            response = requests.post(url, data=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            st.error(f"خطأ في إرسال التلغرام: {e}")
            return False
    else:
        st.warning("يرجى ضبط TELEGRAM_TOKEN و TELEGRAM_CHAT_ID في ملف .env")
        return False

# تنسيق تقرير التلغرام
def format_gainers_for_telegram(df, price_range):
    if df.empty: return None
    message = f"📈 *الأسهم الأكثر ارتفاعاً اليوم*\n\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    message += f"💰 نطاق السعر: ${price_range['min']}-{price_range['max']}\n\n"
    for _, row in df.head(5).iterrows():
        message += (
            f"🔹 *{row['symbol']}* - {row['name']}\n"
            f"▫️ السعر: ${row['price']:.2f}\n"
            f"▫️ التغيير: +{row['change']:.2f} (+{row['changesPercentage']:.2f}%)\n"
            f"───────────────────\n"
        )
    message += "\n📊 *هذه الأسهم ليست توصية مباشرة للشراء*"
    return message

# زر التلغرام
def send_telegram_button(position, price_range):
    if position == "top":
        _, col2 = st.columns([4, 1])
        with col2:
            if st.button("📤 إرسال التقرير إلى التلغرام", key="send_telegram_top"):
                send_report(price_range)
    else:
        st.divider()
        st.subheader("إرسال التقرير")
        if st.button("📤 إرسال التقرير إلى التلغرام", key="send_telegram_bottom"):
            send_report(price_range)

# تقرير التلغرام
def send_report(price_range):
    df = st.session_state.get('gainers', pd.DataFrame())
    if df.empty:
        st.warning("⚠️ لا توجد بيانات حالياً")
        return
    filtered_df = df[~df['name'].str.contains("split|merge|reverse split", case=False, na=False)]
    if not filtered_df.empty:
        message = format_gainers_for_telegram(filtered_df, price_range)
        if send_telegram_message(message):
            st.session_state['telegram_last_sent'] = date.today().isoformat()
            st.toast("✅ تم إرسال التقرير بنجاح!", icon="✅")
        else:
            st.toast("❌ فشل في إرسال الرسالة", icon="❌")
    else:
        st.warning("⚠️ لا توجد أسهم صالحة للإرسال")

# زمن الإرسال التلقائي
def should_send_telegram():
    now = datetime.now()
    return dt_time(17, 0) <= now.time() <= dt_time(17, 5) and \
           st.session_state.get("telegram_last_sent") != date.today().isoformat()

# الشريط الجانبي
with st.sidebar:
    st.header("الإعدادات")
    min_price = st.number_input("🔻 الحد الأدنى للسعر ($)", min_value=0.0, value=1.0)
    max_price = st.number_input("🔺 الحد الأقصى للسعر ($)", min_value=0.0, value=55.0)
    user_api_key = st.text_input("🔑 مفتاح API", value=DEFAULT_API_KEY, type="password")
    price_range = {"min": min_price, "max": max_price}
    if st.button("📨 اختبار التلغرام"):
        df = st.session_state.get('gainers', pd.DataFrame())
        if not df.empty:
            filtered = df[~df['name'].str.contains("split|merge|reverse split", case=False, na=False)]
            msg = format_gainers_for_telegram(filtered.head(3), price_range)
            if send_telegram_message(msg):
                st.toast("✅ تم إرسال رسالة الاختبار", icon="✅")

# جلب البيانات
@st.cache_data(ttl=300)
def get_stock_data(api_key, min_price, max_price):
    try:
        active_url = f"https://financialmodelingprep.com/api/v3/stock_market/actives?apikey={api_key}"
        gainers_url = f"https://financialmodelingprep.com/api/v3/stock_market/gainers?apikey={api_key}"
        active_data = requests.get(active_url).json()
        gainers_data = requests.get(gainers_url).json()
        df_active = pd.DataFrame(active_data)
        df_gainers = pd.DataFrame(gainers_data)
        if 'price' not in df_active or 'price' not in df_gainers:
            return pd.DataFrame(), pd.DataFrame()
        df_active = df_active[(df_active['price'] >= min_price) & (df_active['price'] <= max_price)]
        df_gainers = df_gainers[(df_gainers['price'] >= min_price) & (df_gainers['price'] <= max_price)]
        df_gainers = df_gainers[(df_gainers['change'] > 0) & (df_gainers['changesPercentage'] > 0)]
        return df_active, df_gainers
    except Exception as e:
        st.error(f"❌ خطأ في جلب البيانات: {e}")
        return pd.DataFrame(), pd.DataFrame()

# زر تحديث
if st.button("🔄 تحديث البيانات"):
    st.session_state["active"], st.session_state["gainers"] = get_stock_data(user_api_key, min_price, max_price)

# تحديث تلقائي
st_autorefresh(interval=60000, limit=None, key="auto-refresh")

# جلب مبدئي
if "active" not in st.session_state or "gainers" not in st.session_state:
    st.session_state["active"], st.session_state["gainers"] = get_stock_data(user_api_key, min_price, max_price)

# العنوان
st.title("📈 الأسهم الأمريكية (من 1$ إلى 55$)")

# زر تلغرام أعلى الصفحة
send_telegram_button("top", price_range)

# عرض الأسهم المرتفعة
df_gainers = st.session_state.get("gainers", pd.DataFrame())
if not df_gainers.empty:
    filtered = df_gainers[~df_gainers['name'].str.contains("split|merge|reverse split", case=False, na=False)]
    if not filtered.empty:
        st.subheader("🚀 الأسهم الأكثر ارتفاعاً")
        
        # إنشاء رابط الشارت
        filtered['chart'] = filtered['symbol'].apply(lambda x: f"https://tradingview.com/chart/?symbol={x}")
        
        # عرض الجدول
        st.dataframe(filtered[['symbol', 'name', 'price', 'change', 'changesPercentage', 'chart']],
                     column_config={
                         "symbol": "🔖 الرمز",
                         "name": "🏢 الاسم",
                         "price": st.column_config.NumberColumn("💵 السعر", format="%.2f"),
                         "change": st.column_config.NumberColumn("📊 التغيير", format="%.2f"),
                         "changesPercentage": st.column_config.NumberColumn("📈 النسبة %", format="%.2f%%"),
                         "chart": st.column_config.LinkColumn("📊 الشارت", display_text="عرض")
                     },
                     use_container_width=True, hide_index=True)

        # اختيار السهم أسفل الجدول
        selected = st.selectbox("📌 اختر سهمًا لعرض الشارت:", filtered["symbol"].unique(), key="gainer_chart_select")

        # عرض الشارت تحت الجدول
        show_tradingview_chart(selected)

    else:
        st.info("لا توجد أسهم مؤهلة للعرض.")
else:
    st.warning("لم يتم تحميل البيانات بعد.")

# عرض الأسهم الأكثر تداولاً==========================================================================
#df_active = st.session_state.get("active", pd.DataFrame())
#if not df_active.empty:
#    st.subheader("📊 الأسهم الأكثر تداولاً")
#    col1, col2 = st.columns([3, 1])
#    with col1:
 #       df_active['chart'] = df_active['symbol'].apply(lambda x: f"https://tradingview.com/chart/?symbol={x}")
#        st.dataframe(df_active[['symbol', 'name', 'price', 'change', 'changesPercentage', 'chart']],
#                     column_config={
 #                        "symbol": "🔖 الرمز",
#                         "name": "🏢 الاسم",
#                         "price": st.column_config.NumberColumn("💵 السعر", format="%.2f"),
#                         "change": st.column_config.NumberColumn("📊 التغيير", format="%.2f"),
#                         "changesPercentage": st.column_config.NumberColumn("📈 النسبة %", format="%.2f%%"),
#                         "chart": st.column_config.LinkColumn("📊 الشارت", display_text="عرض")
#                     },
#                     use_container_width=True, hide_index=True)
#    with col2:
#        selected = st.selectbox("📌 اختر سهمًا:", df_active["symbol"].unique())
#        show_tradingview_chart(selected)
#else:
  #  st.warning("لا توجد بيانات للأسهم الأكثر تداولاً.")#

# زر التلغرام أسفل الصفحة
send_telegram_button("bottom", price_range)

# إرسال تلقائي عند الساعة 5
if should_send_telegram():
    filtered = df_gainers[~df_gainers['name'].str.contains("split|merge|reverse split", case=False, na=False)]
    message = format_gainers_for_telegram(filtered, price_range)
    if message and send_telegram_message(message):
        st.session_state["telegram_last_sent"] = date.today().isoformat()
        st.toast("✅ تم الإرسال التلقائي إلى التلغرام", icon="✅")
