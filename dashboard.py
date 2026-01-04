import streamlit as st
import pandas as pd
import psycopg2
import plotly.graph_objects as go
from prediction_engine import predict_match_detailed

# --- إعدادات الصفحة ---
st.set_page_config(page_title="SmartScore Pro Dashboard", layout="wide")

# --- تحسين التصميم (CSS) ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%); color: #2c3e50; }
    .league-header { background: white; padding: 12px; border-radius: 8px; border-right: 6px solid #ff4b4b; margin: 20px 0; font-weight: bold; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .match-row { background: white; padding: 15px; border-radius: 12px; margin-bottom: 5px; display: flex; align-items: center; box-shadow: 0 2px 8px rgba(0,0,0,0.02); }
    .prob-box { background: #FFE0B2; color: #E65100; padding: 6px 12px; border-radius: 8px; font-weight: bold; text-align: center; margin-left: 10px; border: 1px solid #FFCC80; min-width: 65px; }
    .team-logo { width: 30px; height: 30px; margin: 0 10px; }
    .badge { background: #f1f3f5; padding: 4px 10px; border-radius: 5px; font-size: 12px; margin: 2px; border: 1px solid #dee2e6; color: #555; display: inline-block; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_matches():
    try:
        conn = psycopg2.connect("host=localhost dbname=smartscore_db user=postgres password=123456")
        df = pd.read_sql("SELECT * FROM matches WHERE status IN ('TIMED', 'SCHEDULED')", conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"خطأ في الاتصال بقاعدة البيانات: {e}")
        return pd.DataFrame()

st.title("⚽ SmartScore Pro | مركز التحليل المتقدم")

df = load_matches()

if not df.empty:
    # --- الفلتر الجانبي ---
    st.sidebar.header("🔍 تصفية المباريات")
    leagues_list = sorted(df['league'].unique().tolist())
    selected_leagues = st.sidebar.multiselect("اختر الدوري:", leagues_list, default=leagues_list[:2])
    
    filtered_df = df[df['league'].isin(selected_leagues)]

    for league in filtered_df['league'].unique():
        st.markdown(f'<div class="league-header">🏆 {league}</div>', unsafe_allow_html=True)
        
        # نستخدم i هنا لضمان وجود مفتاح فريد لكل مباراة
        for i, row in filtered_df[filtered_df['league'] == league].reset_index().iterrows():
            try:
                data = predict_match_detailed(row['home_team'], row['away_team'])
                p_h, p_d, p_a = data["win_probs"]

                # عرض سطر المباراة (FlashScore)
                st.markdown(f"""
                <div class="match-row">
                    <div style="flex: 2; text-align: right; font-weight: bold;">{row['home_team']} <img src="{row['home_crest']}" class="team-logo"></div>
                    <div style="color: #bdc3c7; font-weight: bold; padding: 0 15px;">VS</div>
                    <div style="flex: 2; font-weight: bold;"><img src="{row['away_crest']}" class="team-logo"> {row['away_team']}</div>
                    <div style="display: flex;">
                        <div class="prob-box">1<br>{p_h*100:.0f}%</div>
                        <div class="prob-box">X<br>{p_d*100:.0f}%</div>
                        <div class="prob-box">2<br>{p_a*100:.0f}%</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # قسم التحليل المعمق مع إضافة مفاتيح فريدة (Unique Keys)
                with st.expander(f"📊 تفاصيل المباراة: {row['home_team']} vs {row['away_team']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**⚽ توزيع الأهداف المتوقع**")
                        h_goals, a_goals = data["goal_dist"]
                        fig_g = go.Figure()
                        fig_g.add_trace(go.Bar(x=list(h_goals.keys()), y=list(h_goals.values()), name="الأرض", marker_color='#FFA726'))
                        fig_g.add_trace(go.Bar(x=list(a_goals.keys()), y=list(a_goals.values()), name="الضيف", marker_color='#FB8C00'))
                        fig_g.update_layout(height=220, margin=dict(t=5,b=5,l=5,r=5), barmode='group', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                        # أضفنا key هنا
                        st.plotly_chart(fig_g, use_container_width=True, key=f"goals_{row['home_team']}_{i}")
                    
                    with col2:
                        st.write("**🟨 توزيع البطاقات الصفراء**")
                        y_cards = data["yellow_dist"]
                        fig_y = go.Figure(go.Bar(x=list(y_cards.keys()), y=list(y_cards.values()), marker_color='#ffd11a'))
                        fig_y.update_layout(height=220, margin=dict(t=5,b=5,l=5,r=5), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                        # أضفنا key هنا أيضاً
                        st.plotly_chart(fig_y, use_container_width=True, key=f"cards_{row['home_team']}_{i}")

                    st.markdown("---")
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.write("**🎯 النتائج المرجحة**")
                        for sc in data["top_scores"]:
                            st.markdown(f'<span class="badge">{sc["score"]} ({sc["prob"]:.1f}%)</span>', unsafe_allow_html=True)
                    with c2:
                        st.write("**🟥 طرد محتمل**")
                        st.error(f"{data['red_prob']:.1f}%")
                    with c3:
                        st.write("**💡 إجمالي الأهداف**")
                        st.info(f"{data['expected_goals']:.2f}")
                
            except Exception as ex:
                continue
else:
    st.info("لا توجد مباريات قادمة لعرضها.")