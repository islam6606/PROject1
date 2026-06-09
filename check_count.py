import sqlite3

def check_database_rows():
    try:
        # الاتصال بقاعدة البيانات
        conn = sqlite3.connect('rainbow_table.db')
        cursor = conn.cursor()
        
        # استعلام للحصول على العدد الإجمالي للأسطر
        cursor.execute("SELECT COUNT(*) FROM rainbow_table")
        total_rows = cursor.fetchone()[0]
        
        print("-" * 40)
        print(f"العدد الفعلي للأسطر داخل القاعدة: {total_rows:,} كلمة مرور.")
        print("-" * 40)
        
        # استعراض عينة من أول 5 أسطر للتأكد من سلامة البيانات
        cursor.execute("SELECT id, original_password, md5_hash FROM rainbow_table LIMIT 5")
        rows = cursor.fetchall()
        
        print("عينة من أول 5 سجلات في القاعدة:")
        for row in rows:
            print(f"ID: {row[0]} | الكلمة: {row[1]} | MD5: {row[2]}")
            
        conn.close()
    except sqlite3.OperationalError:
        print("خطأ: لم يتم العثور على الجدول 'rainbow_table' أو أن الملف غير موجود.")

if __name__ == '__main__':
    check_database_rows()
