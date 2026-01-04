import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from supabase import create_client, Client
import numpy as np

# --- إعدادات الصفحة ---
st.set_page_config(page_title="SmartScore Pro Dashboard", page_icon="⚽", layout="wide")

# --- تحسين التصميم (CSS) ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%); color: #2c3e50; }
    .league-header { background: white; padding: 12px; border-radius: 8px; border-right: 6px solid #ff4b4b; margin: 20px 0; font-weight: bold; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .match-row { background: white; padding: 15px; border-radius: 12px; margin-bottom: 5px; display: flex; align-items: center; box-shadow: 0 2px 8px rgba(0,0,0,0.02); }
    .prob-box { background: #FFE0B2; color: #E65100; padding: 6px 12px; border-radius: 8px; font-weight: bold; text-align: center; margin-left: 10px; border: 1px solid #FFCC80; min-width: 65px; line-height: 1.2; }
    .team-logo { width: 30px; height: 30px; margin: 0 10px; vertical-align: middle; }
    .badge { background: #f1f3f5; padding: 4px 10px; border-radius: 5px; font-size: 12px; margin: 2px; border: 1px solid #dee2e6; color: #555; display: inline-block; }
    </style>
    """, unsafe_allow_html=True)

# --- الربط بـ Supabase ---
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

@st.cache_data(ttl=600)
def load_matches():
    try:
        # جلب المباريات القادمة فقط من السحابة
        response = supabase.table("matches").select("*").execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"خطأ في الاتصال بالسحابة: {e}")
        return pd.DataFrame()

# دالة توقع مبسطة (تحاكي محرك التوقعات بناءً على البيانات المتوفرة)
def get_prediction(home_team, away_team):
    # ملاحظة: في النسخة القادمة سنربطها بمعادلة Poisson الحقيقية
    # حالياً نستخدم أرقاماً مبنية على خوارزمية افتراضية مستقرة
    hash_val = hash(home_team + away_team)
    p_h = abs(hash_val % 50 + 20) / 100
    p_a = abs((hash_val // 2) % 30 + 10) / 100
    p_d = 1.0 - p_h - p_a
    return [p_h, p_d, p_a]

st.title("⚽ SmartScore Pro | مركز التحليل المتقدم")

df = load_matches()

if not df.empty:
    # --- الفلتر الجانبي ---
    st.sidebar.header("🔍 تصفية المباريات")
    leagues_list = sorted(df['league'].unique().tolist())
    selected_leagues = st.sidebar.multiselect("اختر الدوري:", leagues_list, default=leagues_list[:3])
    
    filtered_df = df[df['league'].isin(selected_leagues)]

    for league in filtered_df['league'].unique():
        st.markdown(f'<div class="league-header">🏆 {league}</div>', unsafe_allow_html=True)
        
        league_matches = filtered_df[filtered_df['league'] == league].reset_index()
        for i, row in league_matches.iterrows():
            p_h, p_d, p_a = get_prediction(row['home_team'], row['away_team'])

            # عرض سطر المباراة (FlashScore Style)
            st.markdown(f"""
            <div class="match-row">
                <div style="flex: 2; text-align: right; font-weight: bold;">
                    {row['home_team']} <img src="{row['home_crest']}" class="team-logo">
                </div>
                <div style="color: #bdc3c7; font-weight: bold; padding: 0 15px;">VS</div>
                <div style="flex: 2; font-weight: bold;">
                    <img src="{row['away_crest']}" class="team-logo"> {row['away_team']}
                </div>
                <div style="display: flex;">
                    <div class="prob-box"><small>1</small><br>{p_h*100:.0f}%</div>
                    <div class="prob-box"><small>X</small><br>{p_d*100:.0f}%</div>
                    <div class="prob-box"><small>2</small><br>{p_a*100:.0f}%</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # تفاصيل المباراة
            with st.expander(f"📊 تفاصيل وتحليل: {row['home_team']} vs {row['away_team']}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**⚽ احتمالات الأهداف**")
                    fig = go.Figure(go.Pie(labels=['فوز الأرض', 'تعادل', 'فوز الضيف'], 
                                         values=[p_h, p_d, p_a], hole=.3,
                                         marker_colors=['#ff4b4b', '#bdc3c7', '#3498db']))
                    fig.update_layout(height=200, margin=dict(t=0, b=0, l=0, r=0))
                    st.plotly_chart(fig, use_container_width=True, key=f"chart_{i}_{row['match_id']}")
                
                with col2:
                    st.write("**🎯 نصيحة النظام**")
                    if p_h > p_a:
                        st.success(f"الأفضلية لـ {row['home_team']}")
                    else:
                        st.info(f"الأفضلية لـ {row['away_team']}")
                    st.write(f"إجمالي الأهداف المتوقع: {(p_h+p_a)*2:.2f}")

else:
    st.info("🔄 جاري جلب البيانات من السحابة...")
