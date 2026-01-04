import streamlit as st
import pandas as pd
from supabase import create_client, Client

# إعداد الصفحة
st.set_page_config(page_title="SmartScore AI", page_icon="⚽", layout="wide")

# الربط بـ Supabase عبر Secrets
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

@st.cache_data(ttl=600)
def load_data():
    response = supabase.table("matches").select("*").order("id", desc=True).execute()
    return pd.DataFrame(response.data)

df = load_data()

# --- واجهة المستخدم ---
st.title("⚽ SmartScore AI: التوقعات الذكية")
st.markdown("---")

if not df.empty:
    # تقسيم الشاشة إلى أعمدة لعرض المباريات كبطاقات
    cols = st.columns(2) 
    for index, row in df.head(10).iterrows(): # سنعرض أول 10 مباريات كبداية
        with cols[index % 2]:
            with st.container(border=True):
                st.caption(f"🏆 {row['league']}")
                c1, c2, c3 = st.columns([2, 1, 2])
                
                with c1:
                    st.markdown(f"### {row['home_team']}")
                    st.progress(0.65) # هذه النسبة سنربطها بالذكاء الاصطناعي لاحقاً
                with c2:
                    st.markdown("<h2 style='text-align: center;'>VS</h2>", unsafe_allow_html=True)
                with c3:
                    st.markdown(f"### {row['away_team']}")
                    st.progress(0.35)
                
                # منطقة التوقعات (AI Insights)
                st.info(f"💡 **نصيحة الذكاء الاصطناعي:** احتمالية فوز {row['home_team']} هي الأعلى بناءً على آخر المواجهات.")
else:
    st.warning("لا توجد بيانات حالياً.")
