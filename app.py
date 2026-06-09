from flask import Flask, render_template, request
import hashlib
import os
import sqlite3
import secrets
import time

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
DB_PATH = 'rainbow_table.db'

# ==================== دوال زمايلي ====================

def lookup_hash(hash_val, algo):
    hash_val = hash_val.strip().lower()
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        column_name = f"{algo}_hash"
        query = f"SELECT original_password FROM rainbow_table WHERE {column_name} = ?"
        cursor.execute(query, (hash_val,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None
    except Exception as e:
        print(f"Error searching database: {e}")
        return None

def hash_text(text, algo):
    h = hashlib.new(algo)
    h.update(text.encode())
    return h.hexdigest()

def hash_file(file_path, algo):
    h = hashlib.new(algo)
    with open(file_path, 'rb') as f:
        while chunk := f.read(4096):
            h.update(chunk)
    return h.hexdigest()

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    if request.method == 'POST':
        algo = request.form.get('algo')
        text = request.form.get('text')
        if text:
            if len(text) in [32, 40, 64, 128]:
                cracked = lookup_hash(text, algo)
                if cracked:
                    result = f"تم كسر الهاش بنجاح! الكلمة الأصلية هي: {cracked}"
                else:
                    result = hash_text(text, algo)
            else:
                result = hash_text(text, algo)
        file = request.files.get('file')
        if file and file.filename != '':
            path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(path)
            result = hash_file(path, algo)
    return render_template('index.html', result=result)

# ==================== الجزء بتاعي ====================

def create_index():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_md5    ON rainbow_table(md5_hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sha1   ON rainbow_table(sha1_hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sha256 ON rainbow_table(sha256_hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sha512 ON rainbow_table(sha512_hash)")
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Index error: {e}")

def lookup_hash_timed(hash_val, algo):
    hash_val = hash_val.strip().lower()
    start = time.time()
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        column_name = f"{algo}_hash"
        query = f"SELECT original_password FROM rainbow_table WHERE {column_name} = ?"
        cursor.execute(query, (hash_val,))
        row = cursor.fetchone()
        conn.close()
        result = row[0] if row else None
    except Exception as e:
        print(f"Error: {e}")
        result = None
    elapsed = round(time.time() - start, 4)
    return result, elapsed

def generate_salt():
    return secrets.token_hex(16)

def hash_with_salt(password, salt, algo):
    salted = salt + password
    h = hashlib.new(algo)
    h.update(salted.encode())
    return h.hexdigest()

@app.route('/rainbow', methods=['GET', 'POST'])
def rainbow():
    data = None
    if request.method == 'POST':
        hash_input = request.form.get('hash_input', '').strip()
        algo       = request.form.get('algo', 'md5')
        cracked, elapsed = lookup_hash_timed(hash_input, algo)
        data = {
            'hash_input': hash_input,
            'algo': algo.upper(),
            'cracked': cracked,
            'elapsed': elapsed,
        }
    return render_template('rainbow.html', data=data)

@app.route('/salt', methods=['GET', 'POST'])
def salt_demo():
    demo = None
    if request.method == 'POST':
        password = request.form.get('password')
        algo = request.form.get('algo', 'sha256')
        hash_no_salt = hash_text(password, algo)
        cracked = lookup_hash(hash_no_salt, algo)
        salt = generate_salt()
        hash_salted = hash_with_salt(password, salt, algo)
        cracked_salted = lookup_hash(hash_salted, algo)
        demo = {
            'password': password,
            'algo': algo.upper(),
            'hash_no_salt': hash_no_salt,
            'cracked': cracked,
            'salt': salt,
            'hash_salted': hash_salted,
            'cracked_salted': cracked_salted,
        }
    return render_template('salt.html', demo=demo)

# =====================================================

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.mkdir('uploads')
    create_index()
    app.run(host='0.0.0.0', port=5000, debug=True)
