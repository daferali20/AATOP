import streamlit as st
from dotenv import load_dotenv
import os
import requests
import pandas as pd
import streamlit.components.v1 as components
from datetime import datetime, date, time as dt_time
from streamlit_autorefresh import st_autorefresh

# تحميل المتغيرات من ملف .env
load_dotenv()

# عنوان التطبيق
st.set_page_config(page_title="الأسهم الأكثر تداولاً وارتفاعاً", layout="wide")

# تحميل ملف CSS المخصص
def load_custom_css():
    css = """
    <style>
        /* تنسيق عام */
        body {
            font-family: 'Arial', sans-serif;
            color: #333333;
        }
        h1 {
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }
        .stDataFrame {
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
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
        .css-1d391kg {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
        }
        .telegram-btn {
            background-color: #0088cc !important;
            margin: 10px 0;
        }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

load_custom_css()

# تعريف المتغيرات العامة
min_price = 1.0
max_price = 55.0

# دالة لإنشاء رسالة التلغرام مع إضافة min_price و max_price كمعاملات
def format_gainers_for_telegram(df, price_range):
    if df.empty:
        return None
        
    message = "📈 *الأسهم الأكثر ارتفاعاً اليوم*\n\n"
    message += f"⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    message += f"💰 نطاق السعر: ${price_range['min']}-${price_range['max']}\n\n"
    
    # نحدد أعلى 5 أسهم فقط
    top_gainers = df.head(5)
    
    for _, row in top_gainers.iterrows():
        message += (
            f"🔹 *{row['symbol']}* - {row['name']}\n"
            f"▫️ السعر: ${row['price']:.2f}\n"
            f"▫️ التغيير: +{row['change']:.2f} (+{row['changesPercentage']:.2f}%)\n"
            f"───────────────────\n"
        )
    
    message += "\n📊 *ملاحظة مهمه :* هذه الأسهم ليست توصية  للمضاربه اللحظية قد يؤدي التداول فيها الى خسائر فادحه او ارباح عاليه  انها عالية المخاطر خلك حذر عند التداول فيها او قم بمراجعة القوائم المالية او سبب ارتفاعها"
    return message

# دالة لإرسال التقرير
def send_report(price_range):
    if 'gainers' in st.session_state and not st.session_state['gainers'].empty:
        filtered_df = st.session_state['gainers'][
            ~st.session_state['gainers']['name'].str.contains("split|merge|reverse split", case=False, na=False)
        ]
        if not filtered_df.empty:
            telegram_message = format_gainers_for_telegram(filtered_df, price_range)
            if send_telegram_message(telegram_message):
                st.session_state['telegram_last_sent'] = datetime.now().isoformat()
                st.toast("✅ تم إرسال التقرير إلى التلغرام بنجاح!", icon="✅")
            else:
                st.toast("❌ فشل في إرسال الرسالة", icon="❌")
        else:
            st.warning("⚠️ لا توجد أسهم متاحة للإرسال")
    else:
        st.warning("⚠️ يرجى تحديث البيانات أولاً")

# زر إرسال تلغرام في أعلى الصفحة
def send_telegram_button(position, price_range):
    if position == "top":
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("📤 إرسال التقرير إلى التلغرام", key="send_telegram_top", 
                        help="إرسال قائمة الأسهم الأكثر ارتفاعاً إلى قناة التلغرام"):
                send_report(price_range)
    else:
        st.divider()
        st.subheader("إرسال التقرير")
        if st.button("📤 إرسال التقرير إلى التلغرام", key="send_telegram_bottom", 
                    use_container_width=True, 
                    help="إرسال قائمة الأسهم الأكثر ارتفاعاً إلى قناة التلغرام"):
            send_report(price_range)

# عنوان التطبيق مع زر الإرسال
st.title("📈 الأسهم الأكثر تداولاً وارتفاعاً (1$ إلى 55$)")

# مفاتيح API والتليجرام من .env
#default_api_key = os.getenv("API_KEY", "dIaNorTQjiQuB5D63K2d31yEW8LyxHsz")
default_api_key = os.getenv("API_KEY","CVROqS2TTsTM06ZNpYQJd5C1dXg1Amuv")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

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

def should_send_telegram():
    now = datetime.now()
    send_time_start = dt_time(17, 0)  # 5 مساءً
    send_time_end = dt_time(17, 5)    # حتى 5:05 مساءً
    today = date.today().isoformat()
    
    return (send_time_start <= now.time() <= send_time_end) and \
           (st.session_state.get('telegram_last_sent') != today)

# شريط جانبي للإعدادات
with st.sidebar:
    st.header("الإعدادات")
    min_price = st.number_input("الحد الأدنى للسعر ($)", min_value=0.0, value=1.0, step=0.5)
    max_price = st.number_input("الحد الأقصى للسعر ($)", min_value=0.0, value=55.0, step=0.5)
    user_api_key = st.text_input("مفتاح API (اختياري)", value=default_api_key, type="password")
    
    price_range = {'min': min_price, 'max': max_price}
    
    if st.button("اختبار إرسال تلغرام", key="test_telegram"):
        if 'gainers' in st.session_state and not st.session_state['gainers'].empty:
            filtered_df = st.session_state['gainers'][
                ~st.session_state['gainers']['name'].str.contains("split|merge|reverse split", case=False, na=False)
            ]
            if not filtered_df.empty:
                telegram_message = format_gainers_for_telegram(filtered_df.head(3), price_range)
                if send_telegram_message(telegram_message):
                    st.toast("تم إرسال رسالة الاختبار بنجاح!", icon="✅")
                else:
                    st.toast("فشل في إرسال رسالة الاختبار", icon="❌")
            else:
                st.warning("لا توجد بيانات متاحة للإرسال")
        else:
            st.warning("لا توجد بيانات متاحة للإرسال")
    
    st.markdown("[احصل على مفتاح API مجاني](https://financialmodelingprep.com/developer/docs/)")

api_key = user_api_key if user_api_key else default_api_key

def get_stock_data(api_key, min_price, max_price):
    try:
        active_url = f"https://financialmodelingprep.com/api/v3/stock_market/actives?apikey={api_key}"
        active_data = requests.get(active_url).json()
        
        gainers_url = f"https://financialmodelingprep.com/api/v3/stock_market/gainers?apikey={api_key}"
        gainers_data = requests.get(gainers_url).json()
        
        df_active = pd.DataFrame(active_data)
        df_gainers = pd.DataFrame(gainers_data)
        
        df_active_filtered = df_active[(df_active['price'] >= min_price) & (df_active['price'] <= max_price)]
        df_gainers_filtered = df_gainers[(df_gainers['price'] >= min_price) & (df_gainers['price'] <= max_price)]
        
        df_gainers_filtered = df_gainers_filtered[
            (df_gainers_filtered['change'] > 0) &
            (df_gainers_filtered['changesPercentage'] > 0)
        ]
        
        return df_active_filtered, df_gainers_filtered
        
    except Exception as e:
        st.error(f"حدث خطأ: {e}")
        return pd.DataFrame(), pd.DataFrame()

# زر تحديث البيانات
if st.button("🔄 تحديث البيانات", key="refresh_button"):
    st.session_state['active'], st.session_state['gainers'] = get_stock_data(api_key, min_price, max_price)

# تحديث تلقائي كل 1 دقيقة (60000 مللي ثانية)
count = st_autorefresh(interval=60000, limit=None, key="autorefresh")

# جلب البيانات إذا غير موجودة في الجلسة
if 'active' not in st.session_state or 'gainers' not in st.session_state:
    st.session_state['active'], st.session_state['gainers'] = get_stock_data(api_key, min_price, max_price)

# تصفية الأسهم الأكثر ارتفاعًا
if 'gainers' in st.session_state and not st.session_state['gainers'].empty:
    df = st.session_state['gainers']
    filtered_df = df[~df['name'].str.contains("split|merge|reverse split", case=False, na=False)]

    if not filtered_df.empty:
        st.subheader("📈 الأسهم الأكثر ارتفاعاً (غير مقسّمة أو مدمجة)")
        st.dataframe(
            filtered_df[['symbol', 'name', 'price', 'change', 'changesPercentage']],
            column_config={
                "symbol": "🔖 الرمز",
                "name": "🏢 اسم السهم",
                "price": st.column_config.NumberColumn("💵 السعر ($)", format="%.2f"),
                "change": st.column_config.NumberColumn("📊 التغيير", format="%.2f"),
                "changesPercentage": st.column_config.NumberColumn("📈 النسبة المئوية", format="%.2f%%")
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("لا توجد أسهم مرتفعة غير مقسّمة أو مدمجة حالياً.")
else:
    st.warning("لا توجد بيانات حالياً عن الأسهم الأكثر ارتفاعاً.")

# عرض الأسهم الأكثر تداولًا
import pandas as pd

# عرض الأسهم الأكثر تداولًا
if 'active' in st.session_state:
    st.subheader("الأسهم الأكثر تداولاً")

    if isinstance(st.session_state['active'], pd.DataFrame):
        df = st.session_state['active']
        st.write("🧪 الأعمدة المتوفرة:", df.columns.tolist())
        st.dataframe(df)
    df = df.rename(columns={
        'ticker': 'symbol',
        'companyName': 'name',
        'latestPrice': 'price',
        'changeValue': 'change',
        'changePercent': 'changesPercentage'
        })
        #required_cols = ['symbol', 'name', 'price', 'change', 'changesPercentage']

        if all(col in df.columns for col in required_cols):
            st.dataframe(
                df[required_cols],
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
        else:
            missing = [col for col in required_cols if col not in df.columns]
            st.error(f"❌ الأعمدة التالية مفقودة: {missing}")
    else:
        st.error("❌ المتغير 'active' ليس DataFrame. تحقق من طريقة إنشائه.")


# زر إرسال تلغرام في أسفل الصفحة
send_telegram_button("bottom", price_range)

# تنفيذ إرسال رسالة التليجرام عند الساعة 5 مساءً ولمرة واحدة في اليوم
if 'gainers' in st.session_state and not st.session_state['gainers'].empty:
    filtered_df = st.session_state['gainers'][
        ~st.session_state['gainers']['name'].str.contains("split|merge|reverse split", case=False, na=False)
    ]

    if not filtered_df.empty and should_send_telegram():
        telegram_message = format_gainers_for_telegram(filtered_df, price_range)
        if telegram_message:
            try:
                success = send_telegram_message(telegram_message)
                if success:
                    st.session_state['telegram_last_sent'] = date.today().isoformat()
                    st.toast("✅ تم إرسال رسالة تلغرام بالأسهم المرتفعة تلقائياً", icon="✅")
            except Exception as e:
                st.error(f"❌ خطأ في إرسال التلغرام: {e}")

# شارت TradingView
def render_tradingview_chart():
    with open("tradingview_chart.html", "r") as f:
        html_content = f.read()
        st.components.v1.html(html_content, height=550)

st.title("📈 شارت الأسهم من TradingView")
render_tradingview_chart()

# زر إرسال تلغرام في أعلى الصفحة (بعد تعريف جميع الدوال والمتغيرات)
send_telegram_button("top", price_range)
