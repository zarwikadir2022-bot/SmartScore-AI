import psycopg2

DB_PARAMS = {
    "host": "localhost",
    "database": "smartscore_db",
    "user": "postgres",
    "password": "123456"
}

def analyze_matches():
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()

        # 1. جلب المباريات التي لم تبدأ بعد (TIMED)
        cur.execute("SELECT match_id, home_team, away_team FROM matches WHERE status = 'TIMED'")
        upcoming_matches = cur.fetchall()

        for match in upcoming_matches:
            m_id, home, away = match
            
            # --- منطق التحليل (تجريبي حالياً) ---
            # في المرحلة القادمة، سنسحب "نتائج آخر 5 مباريات" من هنا
            # حالياً سنضع نسباً افتراضية لنختبر النظام
            h_prob, d_prob, a_prob = 0.45, 0.25, 0.30 
            result = "1" if h_prob > a_prob else "2"

            # 2. حفظ التوقع في قاعدة البيانات
            cur.execute("""
                INSERT INTO predictions (match_id, home_win_prob, draw_prob, away_win_prob, predicted_result)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING;
            """, (m_id, h_prob, d_prob, a_prob, result))

        conn.commit()
        print(f"✅ تم تحليل وتوقع {len(upcoming_matches)} مباراة بنجاح!")
        conn.close()

    except Exception as e:
        print(f"❌ خطأ في التحليل: {e}")

if __name__ == "__main__":
    analyze_matches()