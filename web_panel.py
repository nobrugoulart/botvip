import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64

# Configuration
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin')
SECRET_KEY = os.environ.get('SECRET_KEY', 'teste123')

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    if user_id == '1':
        return User(1, ADMIN_USERNAME)
    return None

# Database helper functions
def get_db_connection():
    conn = sqlite3.connect('bot_database.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_dashboard_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get total users
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    # Get VIP users
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_vip = 1")
    vip_users = cursor.fetchone()[0]
    
    # Get total payments
    cursor.execute("SELECT COUNT(*) FROM payments")
    total_payments = cursor.fetchone()[0]
    
    # Get approved payments
    cursor.execute("SELECT COUNT(*) FROM payments WHERE status = 'approved'")
    approved_payments = cursor.fetchone()[0]
    
    # Get total revenue
    cursor.execute("SELECT SUM(amount) FROM payments WHERE status = 'approved'")
    total_revenue = cursor.fetchone()[0] or 0
    
    # Get payment status distribution
    cursor.execute("SELECT status, COUNT(*) FROM payments GROUP BY status")
    payment_status = {row[0]: row[1] for row in cursor.fetchall()}
    
    # Get recent payments
    cursor.execute(
        """SELECT u.username, u.first_name, p.amount, p.status, p.updated_at 
        FROM payments p JOIN users u ON p.user_id = u.user_id 
        ORDER BY p.updated_at DESC LIMIT 10"""
    )
    recent_payments = cursor.fetchall()
    
    # Get payment trend (last 7 days)
    cursor.execute(
        """SELECT DATE(created_at) as date, COUNT(*) as count, SUM(amount) as total
        FROM payments 
        WHERE created_at >= date('now', '-7 days')
        GROUP BY DATE(created_at)
        ORDER BY date"""
    )
    payment_trend = cursor.fetchall()
    
    conn.close()
    
    return {
        'total_users': total_users,
        'vip_users': vip_users,
        'total_payments': total_payments,
        'approved_payments': approved_payments,
        'total_revenue': total_revenue,
        'payment_status': payment_status,
        'recent_payments': recent_payments,
        'payment_trend': payment_trend
    }

def generate_payment_chart():
    conn = get_db_connection()
    df = pd.read_sql_query(
        """SELECT DATE(created_at) as date, COUNT(*) as count
        FROM payments 
        WHERE created_at >= date('now', '-30 days')
        GROUP BY DATE(created_at)
        ORDER BY date""", 
        conn
    )
    conn.close()
    
    if df.empty:
        return None
    
    plt.figure(figsize=(10, 4))
    plt.bar(df['date'], df['count'])
    plt.title('Payments per Day (Last 30 Days)')
    plt.xlabel('Date')
    plt.ylabel('Number of Payments')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()
    
    return base64.b64encode(img.getvalue()).decode()

def generate_revenue_chart():
    conn = get_db_connection()
    df = pd.read_sql_query(
        """SELECT DATE(created_at) as date, SUM(amount) as revenue
        FROM payments 
        WHERE status = 'approved' AND created_at >= date('now', '-30 days')
        GROUP BY DATE(created_at)
        ORDER BY date""", 
        conn
    )
    conn.close()
    
    if df.empty:
        return None
    
    plt.figure(figsize=(10, 4))
    plt.bar(df['date'], df['revenue'])
    plt.title('Revenue per Day (Last 30 Days)')
    plt.xlabel('Date')
    plt.ylabel('Revenue (BRL)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()
    
    return base64.b64encode(img.getvalue()).decode()

# Routes
@app.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            user = User(1, username)
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    stats = get_dashboard_stats()
    payment_chart = generate_payment_chart()
    revenue_chart = generate_revenue_chart()
    
    return render_template(
        'dashboard.html',
        stats=stats,
        payment_chart=payment_chart,
        revenue_chart=revenue_chart
    )

@app.route('/users')
@login_required
def users():
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users ORDER BY is_vip DESC, user_id').fetchall()
    conn.close()
    
    return render_template('users.html', users=users)

@app.route('/user/<int:user_id>')
@login_required
def user_details(user_id):
    conn = get_db_connection()
    
    # Get user information
    user = conn.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
    
    if not user:
        flash('Usuário não encontrado')
        return redirect(url_for('users'))
    
    # Get user payments
    payments = conn.execute(
        '''SELECT * FROM payments 
        WHERE user_id = ? 
        ORDER BY created_at DESC''', 
        (user_id,)
    ).fetchall()
    
    conn.close()
    
    return render_template('user_details.html', user=user, payments=payments)

@app.route('/user/<int:user_id>/grant_vip', methods=['POST'])
@login_required
def grant_vip(user_id):
    # Get settings
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get VIP duration from settings
    cursor.execute("SELECT value FROM settings WHERE key = 'VIP_DURATION'")
    result = cursor.fetchone()
    vip_duration = int(result['value'] if result else 30)  # Default to 30 days
    
    # Get custom duration if provided
    custom_duration = request.form.get('duration')
    if custom_duration and custom_duration.isdigit():
        vip_duration = int(custom_duration)
    
    # Calculate expiry date
    from datetime import timedelta
    expiry_date = datetime.now() + timedelta(days=vip_duration)
    
    # Update user VIP status
    cursor.execute(
        "UPDATE users SET is_vip = 1, expiry_date = ? WHERE user_id = ?",
        (expiry_date, user_id)
    )
    
    conn.commit()
    flash('Status VIP concedido com sucesso')
    
    # Import and call notification function
    import asyncio
    from notifications import notify_vip_access_granted
    
    # Run the async notification function
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(notify_vip_access_granted(user_id, expiry_date))
        loop.close()
        flash('Notificação enviada ao usuário')
    except Exception as e:
        flash(f'Erro ao enviar notificação: {str(e)}')
    
    conn.close()
    
    return redirect(url_for('user_details', user_id=user_id))

@app.route('/user/<int:user_id>/revoke_vip', methods=['POST'])
@login_required
def revoke_vip(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Update user VIP status
    cursor.execute(
        "UPDATE users SET is_vip = 0, expiry_date = NULL WHERE user_id = ?",
        (user_id,)
    )
    
    conn.commit()
    flash('Status VIP revogado com sucesso')
    
    # Import and call notification function
    import asyncio
    from notifications import notify_vip_access_revoked
    
    # Run the async notification function
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(notify_vip_access_revoked(user_id))
        loop.close()
        flash('Notificação de revogação enviada ao usuário')
    except Exception as e:
        flash(f'Erro ao enviar notificação: {str(e)}')
    
    conn.close()
    
    return redirect(url_for('user_details', user_id=user_id))

@app.route('/payments')
@login_required
def payments():
    conn = get_db_connection()
    payments = conn.execute(
        """SELECT p.*, u.username, u.first_name 
        FROM payments p 
        JOIN users u ON p.user_id = u.user_id 
        ORDER BY p.created_at DESC"""
    ).fetchall()
    conn.close()
    
    return render_template('payments.html', payments=payments)

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    # Global declaration at the beginning of the function
    global ADMIN_USERNAME, ADMIN_PASSWORD
    
    # Get current settings
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if settings table exists, if not create it
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    ''')
    conn.commit()
    
    # Default settings
    default_settings = {
        'PAYMENT_AMOUNT': '1',
        'VIP_DURATION': '30',
        'VIP_GROUP_ID': '-1002370145572',
        'ADMIN_USER_ID': '6798939401',
        'MERCADOPAGO_ACCESS_TOKEN': 'APP_USR-4358712787761609-101612-9323686cdb55de2edc92bd6834420501-1001556032',
        'WEBHOOK_URL': '',
        'ADMIN_USERNAME': ADMIN_USERNAME,
        'ADMIN_PASSWORD': ADMIN_PASSWORD
    }
    
    # Load current settings
    current_settings = {}
    for key in default_settings.keys():
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        result = cursor.fetchone()
        if result:
            current_settings[key] = result[0]
        else:
            # Insert default setting if not exists
            cursor.execute("INSERT INTO settings (key, value) VALUES (?, ?)", (key, default_settings[key]))
            current_settings[key] = default_settings[key]
    
    conn.commit()
    
    if request.method == 'POST':
        form_type = request.form.get('form_type', 'bot_settings')
        
        if form_type == 'bot_settings':
            # Update bot settings
            payment_amount = request.form.get('payment_amount')
            vip_duration = request.form.get('vip_duration')
            vip_group_id = request.form.get('vip_group_id')
            admin_user_id = request.form.get('admin_user_id')
            mercadopago_token = request.form.get('mercadopago_token')
            webhook_url = request.form.get('webhook_url')
            
            # Update settings in database
            cursor.execute("UPDATE settings SET value = ? WHERE key = ?", (payment_amount, 'PAYMENT_AMOUNT'))
            cursor.execute("UPDATE settings SET value = ? WHERE key = ?", (vip_duration, 'VIP_DURATION'))
            cursor.execute("UPDATE settings SET value = ? WHERE key = ?", (vip_group_id, 'VIP_GROUP_ID'))
            cursor.execute("UPDATE settings SET value = ? WHERE key = ?", (admin_user_id, 'ADMIN_USER_ID'))
            cursor.execute("UPDATE settings SET value = ? WHERE key = ?", (mercadopago_token, 'MERCADOPAGO_ACCESS_TOKEN'))
            cursor.execute("UPDATE settings SET value = ? WHERE key = ?", (webhook_url, 'WEBHOOK_URL'))
            
        elif form_type == 'admin_settings':
            # Update admin credentials
            admin_username = request.form.get('admin_username')
            admin_password = request.form.get('admin_password')
            
            cursor.execute("UPDATE settings SET value = ? WHERE key = ?", (admin_username, 'ADMIN_USERNAME'))
            
            if admin_password and admin_password.strip():
                cursor.execute("UPDATE settings SET value = ? WHERE key = ?", (admin_password, 'ADMIN_PASSWORD'))
                # Update global variables
                ADMIN_USERNAME = admin_username
                ADMIN_PASSWORD = admin_password
        
        conn.commit()
        flash('Settings updated successfully')
        return redirect(url_for('settings'))
    
    conn.close()
    return render_template('settings.html', config=current_settings)

if __name__ == '__main__':
    app.run(debug=True)