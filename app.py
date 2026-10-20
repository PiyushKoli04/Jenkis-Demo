import os
import sqlite3
import time
from flask import Flask, request, jsonify, render_template, redirect, url_for
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import Counter

app = Flask(__name__)

# Prometheus metrics setup
metrics = PrometheusMetrics(app)
metrics.info('app_info', 'Expense Tracker Application Info', version='1.0.0')

# Custom metric
expenses_added_total = Counter(
    'expenses_added_total',
    'Total number of expenses added to the system'
)

def get_db_path():
    return os.environ.get('DB_PATH', '/data/expenses.db')

def get_db():
    db_path = get_db_path()
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    with conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                date TEXT NOT NULL
            )
        ''')
    conn.close()

# Ensure DB is initialized
init_db()

# --- Health Check ---
@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200

# --- CPU Burn Endpoint for Alert Testing ---
@app.route('/burn', methods=['GET'])
def burn():
    try:
        seconds = int(request.args.get('seconds', 30))
    except (ValueError, TypeError):
        seconds = 30
    seconds = max(1, min(seconds, 120))

    start = time.time()
    # Busy-loop CPU
    while time.time() - start < seconds:
        _ = 999999 * 999999

    return jsonify({"status": "burned", "seconds": seconds}), 200

# --- Web UI Routes ---
@app.route('/', methods=['GET'])
def index():
    conn = get_db()
    expenses = conn.execute('SELECT * FROM expenses ORDER BY date DESC, id DESC').fetchall()
    conn.close()
    total = sum(e['amount'] for e in expenses)
    count = len(expenses)
    # Build category summary for UI stats
    categories = {}
    for e in expenses:
        cat = e['category']
        categories[cat] = categories.get(cat, 0) + e['amount']
    return render_template('index.html', expenses=expenses, total=total, count=count, categories=categories)

@app.route('/add', methods=['GET', 'POST'])
def add_expense():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        amount_str = request.form.get('amount', '').strip()
        category = request.form.get('category', '').strip()
        date = request.form.get('date', '').strip()

        if not title or not amount_str or not category or not date:
            return render_template('add_expense.html', error="All fields are required.")

        try:
            amount = float(amount_str)
        except ValueError:
            return render_template('add_expense.html', error="Amount must be a valid number.")

        conn = get_db()
        with conn:
            conn.execute(
                'INSERT INTO expenses (title, amount, category, date) VALUES (?, ?, ?, ?)',
                (title, amount, category, date)
            )
        conn.close()
        expenses_added_total.inc()
        return redirect(url_for('index'))

    return render_template('add_expense.html')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_expense(id):
    conn = get_db()
    expense = conn.execute('SELECT * FROM expenses WHERE id = ?', (id,)).fetchone()
    if not expense:
        conn.close()
        return redirect(url_for('index'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        amount_str = request.form.get('amount', '').strip()
        category = request.form.get('category', '').strip()
        date = request.form.get('date', '').strip()

        if not title or not amount_str or not category or not date:
            conn.close()
            return render_template('edit_expense.html', expense=expense, error="All fields are required.")

        try:
            amount = float(amount_str)
        except ValueError:
            conn.close()
            return render_template('edit_expense.html', expense=expense, error="Amount must be a valid number.")

        with conn:
            conn.execute(
                'UPDATE expenses SET title = ?, amount = ?, category = ?, date = ? WHERE id = ?',
                (title, amount, category, date, id)
            )
        conn.close()
        return redirect(url_for('index'))

    conn.close()
    return render_template('edit_expense.html', expense=expense)

@app.route('/delete/<int:id>', methods=['GET', 'POST'])
def delete_expense(id):
    conn = get_db()
    with conn:
        conn.execute('DELETE FROM expenses WHERE id = ?', (id,))
    conn.close()
    return redirect(url_for('index'))

# --- REST API Endpoints ---
@app.route('/api/expenses', methods=['GET'])
def api_get_expenses():
    conn = get_db()
    rows = conn.execute('SELECT * FROM expenses ORDER BY date DESC, id DESC').fetchall()
    conn.close()
    expenses = [dict(row) for row in rows]
    return jsonify(expenses), 200

@app.route('/api/expenses/<int:id>', methods=['GET'])
def api_get_expense(id):
    conn = get_db()
    row = conn.execute('SELECT * FROM expenses WHERE id = ?', (id,)).fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Expense not found"}), 404
    return jsonify(dict(row)), 200

@app.route('/api/expenses', methods=['POST'])
def api_create_expense():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid or missing JSON payload"}), 400

    title = data.get('title')
    amount = data.get('amount')
    category = data.get('category')
    date = data.get('date')

    if not title or amount is None or not category or not date:
        return jsonify({"error": "Fields 'title', 'amount', 'category', and 'date' are required"}), 400

    try:
        amount = float(amount)
    except (ValueError, TypeError):
        return jsonify({"error": "Field 'amount' must be a valid number"}), 400

    conn = get_db()
    with conn:
        cursor = conn.execute(
            'INSERT INTO expenses (title, amount, category, date) VALUES (?, ?, ?, ?)',
            (str(title).strip(), amount, str(category).strip(), str(date).strip())
        )
        new_id = cursor.lastrowid
    conn.close()

    expenses_added_total.inc()

    created = {
        "id": new_id,
        "title": str(title).strip(),
        "amount": amount,
        "category": str(category).strip(),
        "date": str(date).strip()
    }
    return jsonify(created), 201

@app.route('/api/expenses/<int:id>', methods=['PUT'])
def api_update_expense(id):
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid or missing JSON payload"}), 400

    conn = get_db()
    row = conn.execute('SELECT * FROM expenses WHERE id = ?', (id,)).fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Expense not found"}), 404

    title = data.get('title')
    amount = data.get('amount')
    category = data.get('category')
    date = data.get('date')

    if not title or amount is None or not category or not date:
        conn.close()
        return jsonify({"error": "Fields 'title', 'amount', 'category', and 'date' are required"}), 400

    try:
        amount = float(amount)
    except (ValueError, TypeError):
        conn.close()
        return jsonify({"error": "Field 'amount' must be a valid number"}), 400

    with conn:
        conn.execute(
            'UPDATE expenses SET title = ?, amount = ?, category = ?, date = ? WHERE id = ?',
            (str(title).strip(), amount, str(category).strip(), str(date).strip(), id)
        )
    conn.close()

    updated = {
        "id": id,
        "title": str(title).strip(),
        "amount": amount,
        "category": str(category).strip(),
        "date": str(date).strip()
    }
    return jsonify(updated), 200

@app.route('/api/expenses/<int:id>', methods=['DELETE'])
def api_delete_expense(id):
    conn = get_db()
    row = conn.execute('SELECT * FROM expenses WHERE id = ?', (id,)).fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Expense not found"}), 404

    with conn:
        conn.execute('DELETE FROM expenses WHERE id = ?', (id,))
    conn.close()

    return jsonify({"message": f"Expense {id} deleted successfully"}), 200

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=False)
