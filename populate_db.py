import sqlite3
import hashlib
import os

# دالة لتوليد الهاشات
def generate_hashes(text):
    return {
        'md5': hashlib.md5(text.encode('utf-8', errors='ignore')).hexdigest(),
        'sha1': hashlib.sha1(text.encode('utf-8', errors='ignore')).hexdigest(),
        'sha256': hashlib.sha256(text.encode('utf-8', errors='ignore')).hexdigest(),
        'sha512': hashlib.sha512(text.encode('utf-8', errors='ignore')).hexdigest()
    }

# دالة بناء القاعدة
def populate():
    file_path = 'rockyou.txt'
    
    if not os.path.exists(file_path):
        print(f"خطأ: ملف {file_path} غير موجود في المجلد!")
        return

    conn = sqlite3.connect('rainbow_table.db')
    cursor = conn.cursor()

    # تحسين أداء SQLite للتعامل مع البيانات الضخمة
    cursor.execute('PRAGMA synchronous = OFF')
    cursor.execute('PRAGMA journal_mode = MEMORY')

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

    batch_size = 20000  # تقليل حجم الدفعة قليلاً لضمان استقرار الذاكرة
    batch_data = []
    count = 0

    print("بدء معالجة الملف، سيتم تخطي أي سطر يحتوي على رموز تالفة...")

    # فتح الملف مع إضافة errors='ignore' لتفادي الانهيار بسبب الرموز الغريبة
    with open(file_path, 'r', encoding='latin-1', errors='ignore') as f:
        for line in f:
            try:
                password = line.strip()
                if not password: 
                    continue
                
                hashes = generate_hashes(password)
                batch_data.append((password, hashes['md5'], hashes['sha1'], hashes['sha256'], hashes['sha512']))
                count += 1

                # عند الوصول للحجم المحدد، يتم الإدخال دفعة واحدة
                if len(batch_data) >= batch_size:
                    cursor.executemany('''
                        INSERT OR IGNORE INTO rainbow_table (original_password, md5_hash, sha1_hash, sha256_hash, sha512_hash)
                        VALUES (?, ?, ?, ?, ?)
                    ''', batch_data)
                    conn.commit()
                    print(f"تمت معالجة وإدخال {count} كلمة...")
                    batch_data = []  # تفريغ الدفعة لافساح المجال في الذاكرة
                    
            except Exception as e:
                # في حال حدوث أي خطأ في سطر معين، يتم طباعته وتخطيه لاستكمال بقية الملف
                print(f"تم تخطي سطر بسبب خطأ: {e}")
                continue

        # إدخال المتبقي من البيانات التي لم تصل لحجم الدفعة الكاملة
        if batch_data:
            cursor.executemany('''
                INSERT OR IGNORE INTO rainbow_table (original_password, md5_hash, sha1_hash, sha256_hash, sha512_hash)
                VALUES (?, ?, ?, ?, ?)
            ''', batch_data)
            conn.commit()

    conn.close()
    print(f"\nتم الانتهاء بنجاح! إجمالي الكلمات المعالجة: {count}")

if __name__ == '__main__':
    populate()
