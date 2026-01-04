import psycopg2
from prediction_engine import predict_match # استيراد المحرك الذي صنعته

DB_PARAMS = {
    "host": "localhost",
    "database": "smartscore_db",
    "user": "postgres",
    "password": "123456"
}

def generate_daily_report():
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()

        # 1. جلب المباريات القادمة فقط من قاعدة البيانات
        cur.execute("SELECT home_team, away_team, league FROM matches WHERE status = 'TIMED'")
        upcoming = cur.fetchall()

        if not upcoming:
            print("📭 لا توجد مباريات قادمة مسجلة في القاعدة حالياً.")
            return

        print(f"\n📊 تقرير الذكاء الاصطناعي لمباريات اليوم ({len(upcoming)} مباراة)")
        print("="*65)
        print(f"{'المباراة':<40} | {'1':<7} | {'X':<7} | {'2':<7}")
        print("-"*65)

        for home, away, league in upcoming:
            try:
                h_win, draw, a_win = predict_match(home, away)
                match_name = f"{home} vs {away}"
                print(f"{match_name[:40]:<40} | {h_win*100:.1f}% | {draw*100:.1f}% | {a_win*100:.1f}%")
            except:
                # في حال كان الفريق جديداً وليس له بيانات تاريخية كافية
                continue

        print("="*65)
        conn.close()

    except Exception as e:
        print(f"❌ خطأ في إنشاء التقرير: {e}")

if __name__ == "__main__":
    generate_daily_report()