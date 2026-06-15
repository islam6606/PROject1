from flask import Flask, render_template, request
import hashlib
import os
import sqlite3
import secrets
import time
import random
import string
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
def check_password_exists(password, algo):
    password_hash = hash_text(password, algo)
    found = lookup_hash(password_hash, algo)
    return found is not None
def analyze_password(password):

    score = 0
    reasons = []

    if len(password) >= 8:
        score += 1
    else:
        reasons.append("Password is too short")

    if any(c.islower() for c in password):
        score += 1
    else:
        reasons.append("No lowercase letters")

    if any(c.isupper() for c in password):
        score += 1
    else:
        reasons.append("No uppercase letters")

    if any(c.isdigit() for c in password):
        score += 1
    else:
        reasons.append("No numbers")

    if any(not c.isalnum() for c in password):
        score += 1
    else:
        reasons.append("No special characters")

    if score <= 2:
        strength = "Weak"
    elif score <= 4:
        strength = "Medium"
    else:
        strength = "Strong"

    suggestion = password

    if not any(c.isupper() for c in password):
        suggestion += "A"

    if not any(c.isdigit() for c in password):
        suggestion += "9"

    if not any(not c.isalnum() for c in password):
        suggestion += "@"

    if len(suggestion) < 8:
        suggestion += "2026"

    found_in_rainbow = check_password_exists(password, 'md5')

    percentage = score * 20

    return strength, reasons, suggestion, found_in_rainbow, percentage
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
@app.route('/checker', methods=['GET', 'POST'])
def checker():
    result = None

    if request.method == 'POST':
        password = request.form.get('password')
        algo = request.form.get('algo', 'sha256')

        exists = check_password_exists(password, algo)

        result = {
            'password': password,
            'algo': algo.upper(),
            'exists': exists
        }

    return render_template('checker.html', result=result)    
@app.route('/strength', methods=['GET', 'POST'])
def strength():

    result = None

    if request.method == 'POST':
        password = request.form.get('password')
        (
           strength_level,
           reasons,
           suggestion,
           found_in_rainbow,
           percentage
        ) = analyze_password(password)  
      
        result = {
          'password': password,
    'strength': strength_level,
    'reasons': reasons,
    'suggestion': suggestion,
    'found_in_rainbow': found_in_rainbow,
    'percentage': percentage

        }

    return render_template('strength.html', result=result)
def generate_password(length, upper, lower, numbers, symbols):

    chars = ""

    if upper:
        chars += string.ascii_uppercase

    if lower:
        chars += string.ascii_lowercase

    if numbers:
        chars += string.digits

    if symbols:
        chars += "!@#$%^&*"

    if not chars:
        return None

    password = ''.join(random.choice(chars) for _ in range(length))

    return password


@app.route('/generator', methods=['GET', 'POST'])
def generator():

    result = None

    if request.method == 'POST':

        length = int(request.form.get('length', 12))

        upper = request.form.get('upper') == 'on'
        lower = request.form.get('lower') == 'on'
        numbers = request.form.get('numbers') == 'on'
        symbols = request.form.get('symbols') == 'on'

        password = generate_password(
            length,
            upper,
            lower,
            numbers,
            symbols
        )

        if password:

            (
                strength_level,
                reasons,
                suggestion,
                found_in_rainbow,
                percentage
            ) = analyze_password(password)

            result = {
                'password': password,
                'strength': strength_level,
                'percentage': percentage,
                'found_in_rainbow': found_in_rainbow
            }

    return render_template('generator.html', result=result)
# =====================================================

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.mkdir('uploads')
    create_index()
    app.run(host='0.0.0.0', port=5000, debug=True)
