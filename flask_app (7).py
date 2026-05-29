from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'change-this-to-something-secret'

DB_PATH = os.path.join(os.path.dirname(__file__), 'zedmart.db')
ADMIN_PASSWORD = 'admin123'
AUTO_APPROVE = False

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        price REAL,
        image_url TEXT,
        description TEXT,
        approved INTEGER DEFAULT 0,
        user_id INTEGER
    )''')
    conn.commit()
    conn.close()

init_db()

def get_whatsapp_link(message):
    number = '26097XXXXXXX'  # Replace with your WhatsApp number
    return f"https://wa.me/{number}?text={message.replace(' ', '%20')}"

@app.route('/')
def index():
    q = request.args.get('q', '').lower()
    conn = get_db()
    if q:
        products = conn.execute("SELECT p.*, u.username FROM products p JOIN users u ON p.user_id=u.id WHERE p.approved=1 AND LOWER(p.name) LIKE ?", ('%'+q+'%',)).fetchall()
    else:
        products = conn.execute("SELECT p.*, u.username FROM products p JOIN users u ON p.user_id=u.id WHERE p.approved=1").fetchall()
    conn.close()
    return render_template('index.html', products=products, q=q, whatsapp_link=get_whatsapp_link)

@app.route('/supplier/register', methods=['GET', 'POST'])
def supplier_register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db()
        try:
            conn.execute("INSERT INTO users (username, password, role) VALUES (?, ?, 'supplier')", (username, password))
            conn.commit()
            flash('Registered! You can now login.')
            return redirect(url_for('supplier_login'))
        except sqlite3.IntegrityError:
            flash('Username already taken.')
        finally:
            conn.close()
    return render_template('supplier_register.html')

@app.route('/supplier/login', methods=['GET', 'POST'])
def supplier_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username=? AND password=? AND role='supplier'", (username, password)).fetchone()
        conn.close()
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = 'supplier'
            return redirect(url_for('supplier_dashboard'))
        flash('Invalid credentials.')
    return render_template('supplier_login.html')

@app.route('/supplier/dashboard', methods=['GET', 'POST'])
def supplier_dashboard():
    if 'role' not in session or session['role'] != 'supplier':
        return redirect(url_for('supplier_login'))

    conn = get_db()
    if request.method == 'POST':
        name = request.form['name']
        price = float(request.form['price'])
        image_url = request.form['image_url']
        description = request.form['description']
        approved = 1 if AUTO_APPROVE else 0
        conn.execute("INSERT INTO products (name, price, image_url, description, approved, user_id) VALUES (?, ?, ?)",
                     (name, price, image_url, description, approved, session['user_id']))
        conn.commit()
        flash('Product added!')

    products = conn.execute("SELECT * FROM products WHERE user_id=?", (session['user_id'],)).fetchall()
    conn.close()
    return render_template('supplier_dashboard.html', products=products, auto_approve=AUTO_APPROVE)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'role' not in session or session['role'] != 'admin':
        if request.method == 'POST' and request.form.get('password') == ADMIN_PASSWORD:
            session['role'] = 'admin'
        else:
            return '<form method="post">Admin Password: <input type="password" name="password"><button>Login</button></form>'

    conn = get_db()
    if request.method == 'POST':
        pid = request.form['id']
        action = request.form['action']
        if action == 'approve':
            conn.execute("UPDATE products SET approved=1 WHERE id=?", (pid,))
        elif action == 'delete':
            conn.execute("DELETE FROM products WHERE id=?", (pid,))
        conn.commit()

    pending = conn.execute("SELECT p.*, u.username FROM products p JOIN users u ON p.user_id=u.id WHERE p.approved=0").fetchall()
    conn.close()
    return render_template('admin.html', pending=pending)

@app.route('/cart/checkout', methods=['POST'])
def cart_checkout():
    data = request.get_json()
    items = data.get('items', [])
    if not items:
        return jsonify({'error': 'Cart empty'}), 400
    msg = "Hi, I want to order:\n"
    total = 0
    for i in items:
        msg += f"- {i['name']} x{i['qty']} = ${i['price']*i['qty']}\n"
        total += i['price'] * i['qty']
    msg += f"\nTotal: ${total}"
    return jsonify({'url': get_whatsapp_link(msg)})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)