import psycopg2

# إعدادات الاتصال (تأكد من وضع كلمة المرور التي اخترتها)
DB_PARAMS = {
    "host": "localhost",
    "database": "smartscore_db",
    "user": "postgres",
    "password": "123456",
    "port": "5432"
}

def create_table():
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        
        # كود SQL لإنشاء الجدول
        query = """
        CREATE TABLE IF NOT EXISTS matches (
            match_id INTEGER PRIMARY KEY,
            home_team TEXT NOT NULL,
            away_team TEXT NOT NULL,
            league TEXT,
            status TEXT,
            match_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        cur.execute(query)
        conn.commit()
        print("✅ تم إنشاء جدول matches بنجاح في PostgreSQL!")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ حدث خطأ: {e}")

if __name__ == "__main__":
    create_table()