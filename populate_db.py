import sqlite3
import hashlib

# دالة لتوليد الهاشات
def generate_hashes(text):
    text = text.strip()
    return {
        'md5': hashlib.md5(text.encode()).hexdigest(),
        'sha1': hashlib.sha1(text.encode()).hexdigest(),
        'sha256': hashlib.sha256(text.encode()).hexdigest(),
        'sha512': hashlib.sha512(text.encode()).hexdigest()
    }

# دالة بناء القاعدة
def populate():
    conn = sqlite3.connect('rainbow_table.db')
    cursor = conn.cursor()

    # إنشاء الجدول
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rainbow_table (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_password TEXT NOT NULL,
            md5_hash TEXT UNIQUE,
            sha1_hash TEXT UNIQUE,
            sha256_hash TEXT UNIQUE,
            sha512_hash TEXT UNIQUE
        )
    ''')

    # تحسين سرعة الأداء لقواعد بيانات SQLite
    cursor.execute('PRAGMA synchronous = OFF')
    cursor.execute('PRAGMA journal_mode = MEMORY')

    batch_data = [] # مصفوفة لتخزين البيانات وضخها جملة واحدة
    count = 0
    target_limit = 200000 # الحد الجديد: أول 200 ألف كلمة مرور فقط
    batch_size = 50000    # حجم الدفعة للإدخال في قاعدة البيانات

    print("بدء قراءة الملف وتوليد الهاشات لأول 200 ألف كلمة...")
    
    try:
        # قراءة الملف سطر بسطر (مرتب من الأكثر شيوعاً للأقل)
        with open('rockyou.txt', 'r', encoding='latin-1') as f:
            for line in f:
                if count >= target_limit:
                    break
                
                password = line.strip()
                if not password: 
                    continue
                
                hashes = generate_hashes(password)
                
                # إضافة البيانات للمصفوفة
                batch_data.append((password, hashes['md5'], hashes['sha1'], hashes['sha256'], hashes['sha512']))
                count += 1
                
                # إدخال البيانات عند الوصول لحجم الدفعة المحدد
                if count % batch_size == 0:
                    cursor.executemany('''
                        INSERT OR IGNORE INTO rainbow_table (original_password, md5_hash, sha1_hash, sha256_hash, sha512_hash)
                        VALUES (?, ?, ?, ?, ?)
                    ''', batch_data)
                    conn.commit() # حفظ التغييرات
                    batch_data = [] # تفريغ المصفوفة للمجموعة القادمة
                    print(f"تمت معالجة وإدخال {count} كلمة بنجاح...")

            # إدخال أي بيانات متبقية لم تصل لحجم الدفعة في نهاية الملف
            if batch_data:
                cursor.executemany('''
                    INSERT OR IGNORE INTO rainbow_table (original_password, md5_hash, sha1_hash, sha256_hash, sha512_hash)
                    VALUES (?, ?, ?, ?, ?)
                ''', batch_data)
                conn.commit()

    except FileNotFoundError:
        print("خطأ: ملف rockyou.txt غير موجود في المجلد الحالي!")
        conn.close()
        return

    conn.close()
    print(f"تم الانتهاء بنجاح! القاعدة تحتوي الآن على {count} كلمة مرور من الأكثر شيوعاً.")

if __name__ == '__main__':
    populate()
