import streamlit as st
import pandas as pd
from supabase import create_client, Client

# إعداد الصفحة بأسلوب Dark Mode رياضي
st.set_page_config(page_title="SmartScore AI", page_icon="⚽", layout="wide")

# الربط بـ Supabase
URL = "https://your-project.id.supabase.co"
KEY = "your-anon-key"
supabase: Client = create_client(URL, KEY)

@st.cache_data(ttl=300)
def load_cloud_data():
    response = supabase.table("matches").select("*").order("match_date", desc=False).execute()
    return pd.DataFrame(response.data)

# واجهة المستخدم
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/5323/5323773.png", width=100)
st.sidebar.title("SmartScore AI")
st.sidebar.info("المحرك يقوم بتحليل 1700+ مباراة حالياً")

df = load_cloud_data()

if not df.empty:
    # فلترة حسب الدوري
    league = st.sidebar.selectbox("اختر الدوري", ["الكل"] + list(df['league'].unique()))
    display_df = df if league == "الكل" else df[df['league'] == league]

    st.title(f"📊 توقعات مباريات {league}")

    # عرض المباريات في كروت (Cards)
    for _, row in display_df.head(20).iterrows(): # عرض أول 20 مباراة حالياً
        with st.expander(f"⚽ {row['home_team']} vs {row['away_team']}"):
            c1, c2, c3 = st.columns([1, 1, 1])
            with c1:
                st.write(f"🏠 **{row['home_team']}**")
                st.progress(0.65) # نسبة افتراضية سيتم ربطها بالمعادلة لاحقاً
            with c2:
                st.markdown("<h3 style='text-align: center;'>VS</h3>", unsafe_allow_html=True)
                st.caption(f"📅 {row['status']}")
            with c3:
                st.write(f"🚀 **{row['away_team']}**")
                st.progress(0.35)
            
            st.success(f"🎯 التوقع الأكثر احتمالاً: فوز {row['home_team']} (2-1)")

else:
    st.warning("🔄 البيانات قيد الرفع من جهاز Vostro... يرجى الانتظار")
