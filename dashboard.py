import streamlit as st
import pandas as pd
from supabase import create_client, Client

# إعداد الصفحة
st.set_page_config(page_title="SmartScore AI", layout="wide")

# دالة للتحقق من وجود الـ Secrets
def get_supabase_client():
    try:
        # محاولة جلب البيانات من Secrets
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception:
        return None

supabase = get_supabase_client()

if supabase is None:
    st.error("❌ خطأ في الإعدادات: يرجى التأكد من إضافة SUPABASE_URL و SUPABASE_KEY في إعدادات Secrets على Streamlit Cloud.")
    st.stop()

@st.cache_data(ttl=600)
def load_cloud_data():
    try:
        # جلب أول 100 مباراة للتجربة
        response = supabase.table("matches").select("*").limit(100).execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"❌ تعذر الاتصال بـ Supabase: {str(e)}")
        return pd.DataFrame()

st.title("⚽ SmartScore AI - لوحة التحكم السحابية")

df = load_cloud_data()

if not df.empty:
    st.success(f"📈 تم تحميل {len(df)} مباراة بنجاح من السحابة!")
    st.dataframe(df)
else:
    st.info("🔄 في انتظار البيانات... تأكد من رفع المباريات من جهازك الـ Vostro.")
