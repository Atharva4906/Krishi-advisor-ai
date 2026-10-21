# app.py — KrishiAdvisor V2
# Multi-page Flask application for Indian farmers

import os, json, hashlib, datetime, urllib.error, urllib.request
from functools import wraps
from dotenv import load_dotenv
from flask import (Flask, render_template, request, jsonify,
                   redirect, url_for, session, flash, g)
from database import get_db, init_db, seed_price_history
from ai_engine import full_analysis, predict_prices

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'development-only-secret')
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
# Initialize DB on startup (required for Vercel)
init_db()
seed_price_history()


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def hash_pw(pw): return hashlib.sha256(pw.encode()).hexdigest()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('कृपया आधी लॉगिन करा / Please login first', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def get_current_user():
    if 'user_id' not in session:
        return None
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id=?', (session['user_id'],)).fetchone()
    conn.close()
    return user

def get_all_crops():
    conn   = get_db()
    crops  = conn.execute('SELECT * FROM crops ORDER BY name_en').fetchall()
    conn.close()
    return crops


# ══════════════════════════════════════════════════════════════════════════════
#  PUBLIC PAGES
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/')
def home():
    user  = get_current_user()
    crops = get_all_crops()
    return render_template('home.html', user=user, crops=crops)

@app.route('/about')
def about():
    return render_template('about.html', user=get_current_user())


# ══════════════════════════════════════════════════════════════════════════════
#  AUTH
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name     = (request.form.get('name') or '').strip()
        phone    = (request.form.get('phone') or '').strip()
        village  = (request.form.get('village') or '').strip()
        district = (request.form.get('district') or '').strip()
        password = (request.form.get('password') or '')

        # Keep only digits in phone
        phone_digits = ''.join(filter(str.isdigit, phone))

        if not name:
            flash('❌ नाव भरणे आवश्यक आहे / Name is required', 'danger')
            return render_template('register.html')
        if len(phone_digits) < 10:
            flash('❌ १० अंकी मोबाइल नंबर भरा / Enter valid 10-digit mobile number', 'danger')
            return render_template('register.html')
        if len(password) < 4:
            flash('❌ पासवर्ड किमान ४ अक्षरांचा असावा / Password must be at least 4 characters', 'danger')
            return render_template('register.html')

        try:
            conn = get_db()
            existing = conn.execute('SELECT id FROM users WHERE phone=?', (phone_digits,)).fetchone()
            if existing:
                conn.close()
                flash('❌ हा मोबाइल नंबर आधीच नोंदणीकृत आहे / Phone already registered. Please login.', 'danger')
                return render_template('register.html')

            conn.execute(
                'INSERT INTO users (name, phone, village, district, password_hash, lang) VALUES (?,?,?,?,?,?)',
                (name, phone_digits, village, district, hash_pw(password), 'mr')
            )
            conn.commit()
            conn.close()
            flash(f'✅ नोंदणी यशस्वी! {name} जी, आता लॉगिन करा / Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'❌ नोंदणी अयशस्वी / Registration failed: {str(e)}', 'danger')
            return render_template('register.html')

    return render_template('register.html')


@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        phone    = ''.join(filter(str.isdigit, (request.form.get('phone') or '')))
        password = (request.form.get('password') or '')

        if not phone:
            flash('❌ मोबाइल नंबर भरा / Enter mobile number', 'danger')
            return render_template('login.html')
        if not password:
            flash('❌ पासवर्ड भरा / Enter password', 'danger')
            return render_template('login.html')

        try:
            conn         = get_db()
            phone_exists = conn.execute('SELECT id FROM users WHERE phone=?', (phone,)).fetchone()
            if not phone_exists:
                conn.close()
                flash('❌ हा नंबर नोंदणीकृत नाही / Phone not registered. Please register first.', 'danger')
                return render_template('login.html')

            user = conn.execute(
                'SELECT * FROM users WHERE phone=? AND password_hash=?',
                (phone, hash_pw(password))
            ).fetchone()
            conn.close()

            if user:
                session.clear()
                session['user_id']   = user['id']
                session['user_name'] = user['name']
                session.permanent    = True
                flash(f'✅ स्वागत आहे {user["name"]}! / Welcome {user["name"]}!', 'success')
                return redirect(url_for('dashboard'))

            flash('❌ चुकीचा पासवर्ड / Wrong password. Try again.', 'danger')
        except Exception as e:
            flash(f'❌ लॉगिन त्रुटी / Login error: {str(e)}', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('लॉगआउट यशस्वी / Logged out successfully', 'info')
    return redirect(url_for('home'))


# ══════════════════════════════════════════════════════════════════════════════
#  FARMER DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/dashboard')
@login_required
def dashboard():
    uid  = session['user_id']
    conn = get_db()

    # Summary stats
    total_sales = conn.execute(
        'SELECT COALESCE(SUM(total_amount),0) as t FROM sales WHERE user_id=?',(uid,)
    ).fetchone()['t']
    total_profit = conn.execute(
        'SELECT COALESCE(SUM(profit),0) as t FROM sales WHERE user_id=?',(uid,)
    ).fetchone()['t']
    active_stock = conn.execute(
        'SELECT COUNT(*) as c FROM stock WHERE user_id=? AND status="stored"',(uid,)
    ).fetchone()['c']
    pred_count = conn.execute(
        'SELECT COUNT(*) as c FROM predictions WHERE user_id=?',(uid,)
    ).fetchone()['c']

    # Recent sales (last 5)
    recent_sales = conn.execute('''
        SELECT s.*, c.name_en, c.name_mr FROM sales s
        JOIN crops c ON s.crop_id=c.id
        WHERE s.user_id=? ORDER BY s.created_at DESC LIMIT 5
    ''', (uid,)).fetchall()

    # Monthly profit chart data (last 6 months)
    monthly = conn.execute('''
        SELECT strftime('%Y-%m', sale_date) as mo, SUM(profit) as p
        FROM sales WHERE user_id=?
        GROUP BY mo ORDER BY mo DESC LIMIT 6
    ''', (uid,)).fetchall()

    # Stock summary
    stocks = conn.execute('''
        SELECT st.*, c.name_en, c.name_mr FROM stock st
        JOIN crops c ON st.crop_id=c.id
        WHERE st.user_id=? AND st.status="stored"
        ORDER BY st.created_at DESC LIMIT 5
    ''', (uid,)).fetchall()
    upcoming_plans = conn.execute('''
        SELECT fp.*, c.name_en, c.name_mr
        FROM farm_plans fp JOIN crops c ON fp.crop_id=c.id
        WHERE fp.user_id=? AND fp.status='planned'
        ORDER BY COALESCE(fp.expected_harvest, fp.sowing_date) ASC LIMIT 4
    ''', (uid,)).fetchall()
    total_expenses = conn.execute(
        'SELECT COALESCE(SUM(amount),0) AS total FROM farm_expenses WHERE user_id=?',
        (uid,)
    ).fetchone()['total']

    conn.close()

    # Convert SQLite Row objects to plain dicts (required for tojson in template)
    recent_sales = [dict(r) for r in recent_sales]
    monthly      = [{'mo': r['mo'], 'p': float(r['p'] or 0)} for r in monthly]
    stocks       = [dict(r) for r in stocks]
    upcoming_plans = [dict(r) for r in upcoming_plans]
    today = datetime.date.today()
    alerts = []
    reminders = []
    for stock_item in stocks:
        quantity = float(stock_item.get('quantity_kg') or 0)
        if quantity < 50:
            alerts.append({
                'title': f"कमी साठा: {stock_item['name_mr'] or stock_item['name_en']}",
                'text': f"फक्त {quantity:g} kg शिल्लक आहे. / Only {quantity:g} kg remains.",
                'level': 'warning'
            })
        harvest_date = stock_item.get('harvest_date')
        if harvest_date:
            try:
                harvest = datetime.date.fromisoformat(harvest_date)
                age_days = (today - harvest).days
                if age_days >= 30:
                    reminders.append({
                        'title': f"साठा तपासा: {stock_item['name_mr'] or stock_item['name_en']}",
                        'text': f"कापणीला {age_days} दिवस झाले. विक्री किंवा AI सल्ला तपासा.",
                        'link': f"/advisor?crop={stock_item['name_en']}"
                    })
            except ValueError:
                pass
    if not stocks:
        reminders.append({
            'title': 'पहिला साठा जोडा / Add your first stock',
            'text': 'साठा जोडल्यावर तुम्हाला वैयक्तिक विक्री आणि AI सूचना मिळतील.',
            'link': '/stock'
        })
    month = today.month
    seasonal = [
        ('हंगामी नियोजन', 'पावसाळ्यापूर्वी साठवणूक जागा आणि वाहतूक खर्च तपासा.'),
        ('हंगामी नियोजन', 'साठवलेला माल नियमित तपासा आणि बाजारभावाशी तुलना करा.'),
        ('हंगामी नियोजन', 'विक्रीपूर्वी पुढील ४ महिन्यांचा AI भाव अंदाज पहा.')
    ][(month - 1) % 3]

    return render_template('dashboard.html',
        user=get_current_user(),
        total_sales=round(float(total_sales or 0), 2),
        total_profit=round(float(total_profit or 0), 2),
        active_stock=int(active_stock or 0),
        pred_count=int(pred_count or 0),
        recent_sales=recent_sales,
        monthly=monthly,
        stocks=stocks,
        upcoming_plans=upcoming_plans,
        total_expenses=round(float(total_expenses or 0), 2),
        alerts=alerts,
        reminders=reminders,
        seasonal_outlook=seasonal
    )


# ══════════════════════════════════════════════════════════════════════════════
#  STOCK MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/stock')
@login_required
def stock():
    uid    = session['user_id']
    conn   = get_db()
    stocks = conn.execute('''
        SELECT st.*, c.name_en, c.name_mr, c.category FROM stock st
        JOIN crops c ON st.crop_id=c.id
        WHERE st.user_id=? ORDER BY st.created_at DESC
    ''', (uid,)).fetchall()
    crops  = get_all_crops()
    conn.close()
    return render_template('stock.html', user=get_current_user(),
                           stocks=stocks, crops=crops)


# ══════════════════════════════════════════════════════════════════════════════
#  FARM PLANNER AND EXPENSES
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/planner', methods=['GET', 'POST'])
@login_required
def planner():
    uid = session['user_id']
    if request.method == 'POST':
        try:
            crop_id = int(request.form.get('crop_id') or 0)
            area = float(request.form.get('area_acres') or 0)
            if crop_id <= 0 or area <= 0:
                raise ValueError('Crop and positive area are required')
            conn = get_db()
            conn.execute('''
                INSERT INTO farm_plans
                (user_id,crop_id,area_acres,sowing_date,expected_harvest,
                 irrigation_plan,soil_type,notes)
                VALUES (?,?,?,?,?,?,?,?)
            ''', (uid, crop_id, area, request.form.get('sowing_date', '').strip(),
                  request.form.get('expected_harvest', '').strip(),
                  request.form.get('irrigation_plan', '').strip(),
                  request.form.get('soil_type', '').strip(),
                  request.form.get('notes', '').strip()))
            conn.commit()
            conn.close()
            flash('पीक नियोजन जतन झाले / Crop plan saved', 'success')
        except (ValueError, TypeError) as e:
            flash(f'नियोजन तपासा / Check crop plan: {e}', 'danger')
        return redirect(url_for('planner'))

    conn = get_db()
    plans = conn.execute('''
        SELECT fp.*, c.name_en, c.name_mr FROM farm_plans fp
        JOIN crops c ON fp.crop_id=c.id WHERE fp.user_id=?
        ORDER BY COALESCE(fp.expected_harvest, fp.sowing_date) ASC
    ''', (uid,)).fetchall()
    expenses = conn.execute('''
        SELECT fe.*, fp.id AS plan_number, c.name_mr, c.name_en
        FROM farm_expenses fe
        LEFT JOIN farm_plans fp ON fe.plan_id=fp.id
        LEFT JOIN crops c ON fp.crop_id=c.id
        WHERE fe.user_id=? ORDER BY COALESCE(fe.expense_date, fe.created_at) DESC LIMIT 30
    ''', (uid,)).fetchall()
    total_expenses = conn.execute(
        'SELECT COALESCE(SUM(amount),0) AS total FROM farm_expenses WHERE user_id=?',
        (uid,)
    ).fetchone()['total']
    conn.close()
    return render_template('planner.html', user=get_current_user(),
                           crops=get_all_crops(), plans=plans,
                           expenses=expenses, total_expenses=total_expenses)


@app.route('/planner/expense', methods=['POST'])
@login_required
def add_expense():
    try:
        amount = float(request.form.get('amount') or 0)
        if amount <= 0:
            raise ValueError('Amount must be greater than zero')
        plan_id = request.form.get('plan_id') or None
        conn = get_db()
        if plan_id:
            owned = conn.execute(
                'SELECT id FROM farm_plans WHERE id=? AND user_id=?',
                (int(plan_id), session['user_id'])
            ).fetchone()
            if not owned:
                conn.close()
                flash('Invalid crop plan', 'danger')
                return redirect(url_for('planner'))
        conn.execute('''
            INSERT INTO farm_expenses
            (user_id,plan_id,category,amount,expense_date,notes)
            VALUES (?,?,?,?,?,?)
        ''', (session['user_id'], plan_id,
              request.form.get('category', 'Other').strip() or 'Other',
              amount, request.form.get('expense_date', '').strip(),
              request.form.get('notes', '').strip()))
        conn.commit()
        conn.close()
        flash('खर्च नोंदवला / Expense recorded', 'success')
    except (ValueError, TypeError) as e:
        flash(f'खर्च तपासा / Check expense: {e}', 'danger')
    return redirect(url_for('planner'))


@app.route('/stock/add', methods=['POST'])
@login_required
def add_stock():
    uid = session['user_id']
    try:
        def safe_float(val, default=0.0):
            """Convert form value to float safely — handles empty strings."""
            try:
                return float(val) if val and str(val).strip() != '' else default
            except (ValueError, TypeError):
                return default

        crop_id      = int(request.form.get('crop_id', 1))
        quantity_kg  = safe_float(request.form.get('quantity_kg'), 0.0)
        if quantity_kg <= 0:
            flash('प्रमाण (quantity) योग्य भरा / Please enter valid quantity', 'danger')
            return redirect(url_for('stock'))

        conn = get_db()
        conn.execute('''
            INSERT INTO stock
            (user_id, crop_id, quantity_kg, purchase_price, production_cost,
             harvest_date, storage_type, notes, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'stored')
        ''', (
            uid,
            crop_id,
            quantity_kg,
            safe_float(request.form.get('purchase_price')),
            safe_float(request.form.get('production_cost')),
            request.form.get('harvest_date', '').strip(),
            request.form.get('storage_type', 'home'),
            request.form.get('notes', '').strip(),
        ))
        conn.commit()
        conn.close()
        flash('✅ माल साठा यशस्वीरित्या जोडला! / Stock added successfully!', 'success')
    except Exception as e:
        flash(f'Error saving stock: {str(e)}', 'danger')
    return redirect(url_for('stock'))


@app.route('/stock/sell/<int:stock_id>', methods=['POST'])
@login_required
def sell_stock(stock_id):
    uid = session['user_id']
    try:
        conn  = get_db()
        st    = conn.execute('SELECT * FROM stock WHERE id=? AND user_id=?',
                             (stock_id, uid)).fetchone()
        if not st:
            flash('Stock not found', 'danger')
            return redirect(url_for('stock'))

        qty        = float(request.form.get('quantity_kg') or 0)
        sale_price = float(request.form.get('sale_price') or 0)
        if qty <= 0 or sale_price <= 0:
            flash('योग्य प्रमाण आणि भाव भरा / Enter valid quantity and price', 'danger')
            return redirect(url_for('stock'))
        total  = qty * sale_price
        cost   = float(st['production_cost'] or 0)
        profit = total - cost * qty

        conn.execute('''
            INSERT INTO sales
            (user_id,stock_id,crop_id,quantity_kg,sale_price,total_amount,
             buyer,sale_date,profit,notes)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        ''', (uid, stock_id, st['crop_id'], qty, sale_price, total,
              request.form.get('buyer',''),
              request.form.get('sale_date', datetime.date.today().isoformat()),
              round(profit, 2), request.form.get('notes','')))

        # Update stock quantity
        new_qty = st['quantity_kg'] - qty
        if new_qty <= 0:
            conn.execute('UPDATE stock SET status="sold" WHERE id=?', (stock_id,))
        else:
            conn.execute('UPDATE stock SET quantity_kg=? WHERE id=?', (new_qty, stock_id))

        conn.commit()
        conn.close()
        flash(f'विक्री नोंदवली! नफा: ₹{profit:.0f} / Sale recorded! Profit: ₹{profit:.0f}', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('stock'))


# ══════════════════════════════════════════════════════════════════════════════
#  SALES HISTORY
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/sales')
@login_required
def sales():
    uid   = session['user_id']
    conn  = get_db()
    rows  = conn.execute('''
        SELECT s.*, c.name_en, c.name_mr FROM sales s
        JOIN crops c ON s.crop_id=c.id
        WHERE s.user_id=? ORDER BY s.created_at DESC
    ''', (uid,)).fetchall()

    total_profit = conn.execute(
        'SELECT COALESCE(SUM(profit),0) as t FROM sales WHERE user_id=?',(uid,)
    ).fetchone()['t']
    conn.close()
    return render_template('sales.html', user=get_current_user(),
                           sales=rows, total_profit=total_profit)


# ══════════════════════════════════════════════════════════════════════════════
#  AI ADVISOR PAGE
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/advisor')
def advisor():
    crops = get_all_crops()
    history = []
    if 'user_id' in session:
        conn = get_db()
        history = conn.execute('''
            SELECT p.id, p.quantity, p.current_price, p.best_strategy,
                   p.expected_profit, p.risk_level, p.result_json, p.created_at,
                   c.name_en, c.name_mr
            FROM predictions p
            JOIN crops c ON p.crop_id=c.id
            WHERE p.user_id=? ORDER BY p.created_at DESC LIMIT 8
        ''', (session['user_id'],)).fetchall()
        conn.close()
        history = [dict(row) for row in history]
    return render_template('advisor.html', user=get_current_user(),
                           crops=crops, history=history)


@app.route('/api/predictions/<int:prediction_id>')
@login_required
def api_prediction(prediction_id):
    conn = get_db()
    row = conn.execute('''
        SELECT result_json FROM predictions WHERE id=? AND user_id=?
    ''', (prediction_id, session['user_id'])).fetchone()
    conn.close()
    if not row:
        return jsonify({'error': 'Analysis not found'}), 404
    try:
        return jsonify(json.loads(row['result_json']))
    except (TypeError, json.JSONDecodeError):
        return jsonify({'error': 'Saved analysis is invalid'}), 500


@app.route('/api/predict', methods=['POST'])
def api_predict():
    try:
        d = request.get_json() or request.form.to_dict()

        crop_name = str(d.get('crop_name', 'onion')).lower().strip()
        qty       = float(d.get('quantity', 100) or 100)
        buy_price = float(d.get('current_price', 10) or 10)
        prod_cost = float(d.get('production_cost', 0) or 0)
        transport = float(d.get('transport_cost', 2) or 2)
        storage   = float(d.get('storage_cost', 2) or 2)
        temp      = str(d.get('temperature', 'medium') or 'medium')

        # Always resolve crop_id from DB by name — prevents FOREIGN KEY error
        conn     = get_db()
        crop_row = conn.execute('SELECT id FROM crops WHERE name_en=?', (crop_name,)).fetchone()
        if not crop_row:
            crop_row = conn.execute('SELECT id FROM crops WHERE name_en LIKE ?', (f'%{crop_name}%',)).fetchone()
        crop_id = crop_row['id'] if crop_row else 1
        conn.close()

        user_prices = []
        for k in ['past_price_1', 'past_price_2', 'past_price_3']:
            v = d.get(k)
            if v:
                try: user_prices.append(float(v))
                except: pass

        result = full_analysis(
            crop_id, crop_name, qty, buy_price, prod_cost,
            transport, storage, temp,
            user_prices if user_prices else None
        )

        # Save to DB — wrapped so it never blocks the result
        if 'user_id' in session:
            try:
                conn = get_db()
                conn.execute('''
                    INSERT INTO predictions
                    (user_id,crop_id,quantity,current_price,best_strategy,
                     expected_profit,risk_level,result_json)
                    VALUES (?,?,?,?,?,?,?,?)
                ''', (session['user_id'], crop_id, qty, buy_price,
                      result['best_strategy'], result['expected_profit'],
                      result['risk'], json.dumps(result)))
                conn.commit()
                conn.close()
            except Exception:
                pass  # logging failure must never block the AI result

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/ai-advice', methods=['POST'])
@app.route('/api/groq-advice', methods=['POST'])
def api_groq_advice():
    """Generate farmer-friendly advice using Groq without exposing the API key."""
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        return jsonify({'error': 'AI provider is not configured on the Flask server'}), 503

    data = request.get_json() or {}
    required = ('crop_name', 'quantity', 'current_price', 'analysis')
    if any(key not in data for key in required):
        return jsonify({'error': 'crop_name, quantity, current_price and analysis are required'}), 400

    prompt = f"""
You are KrishiAdvisor, a careful agricultural assistant for a Maharashtra farmer.
Give practical, concise advice in Marathi first, followed by English.
Do not invent live weather or market data. Clearly say when the farmer should
verify local mandi prices, an agriculture officer, or a soil expert.

Crop: {data['crop_name']}
Quantity: {data['quantity']} kg
Current price: ₹{data['current_price']}/kg
AI numerical analysis: {json.dumps(data['analysis'], ensure_ascii=False)}

Return exactly these sections:
1. निर्णय / Decision
2. पुढील 3 कृती / Next 3 actions
3. जोखीम / Risks
4. स्थानिक पडताळणी / Local verification
"""
    payload = json.dumps({
        'model': os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile'),
        'messages': [
            {'role': 'system', 'content': 'You provide safe, evidence-aware farm guidance.'},
            {'role': 'user', 'content': prompt}
        ],
        'temperature': 0.3,
        'max_tokens': 700
    }).encode('utf-8')
    req = urllib.request.Request(
        'https://api.groq.com/openai/v1/chat/completions',
        data=payload,
        headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
        method='POST'
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
        advice = result['choices'][0]['message']['content']
        return jsonify({'advice': advice, 'model': result.get('model')})
    except (urllib.error.HTTPError, urllib.error.URLError, KeyError, IndexError, json.JSONDecodeError) as exc:
        return jsonify({'error': f'Groq advice request failed: {exc}'}), 502


@app.route('/api/ai-farm-help', methods=['POST'])
def api_ai_farm_help():
    """Answer a bounded farmer question without exposing the AI provider key."""
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        return jsonify({'error': 'AI provider is not configured on the Flask server'}), 503

    data = request.get_json() or {}
    question = str(data.get('question') or '').strip()
    if not question:
        return jsonify({'error': 'A farmer question is required'}), 400
    if len(question) > 1200:
        return jsonify({'error': 'Question must be 1200 characters or less'}), 400

    crop_name = str(data.get('crop_name') or 'Not specified').strip()
    language = 'Marathi first, followed by English' if data.get('language', 'mr') == 'mr' else 'English'
    context = data.get('context') or {}
    prompt = f"""
You are KrishiAdvisor, a careful agricultural assistant for a Maharashtra farmer.
Answer in {language}. Give practical steps suitable for a small or medium farm.
Do not claim live weather, market, pesticide approval, or disease diagnosis.
For chemical, disease, legal, or emergency questions, recommend confirming with
an agriculture officer, soil lab, or qualified agronomist. Do not recommend
unsafe chemical combinations or unsupported dosages.

Crop: {crop_name}
Farmer context: {json.dumps(context, ensure_ascii=False)}
Question: {question}

Return exactly these sections:
1. थोडक्यात उत्तर / Short answer
2. आजची कृती / What to do today
3. पुढील 7 दिवस / Next 7 days
4. काळजी / Safety and verification
"""
    payload = json.dumps({
        'model': os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile'),
        'messages': [
            {'role': 'system', 'content': 'You provide safe, evidence-aware farm guidance.'},
            {'role': 'user', 'content': prompt}
        ],
        'temperature': 0.25,
        'max_tokens': 850
    }).encode('utf-8')
    req = urllib.request.Request(
        'https://api.groq.com/openai/v1/chat/completions',
        data=payload,
        headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
        method='POST'
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
        advice = result['choices'][0]['message']['content']
        return jsonify({'advice': advice, 'model': result.get('model')})
    except (urllib.error.HTTPError, urllib.error.URLError, KeyError, IndexError, json.JSONDecodeError) as exc:
        return jsonify({'error': f'AI farm help request failed: {exc}'}), 502


@app.route('/api/crops')
def api_crops():
    crops = get_all_crops()
    return jsonify([dict(c) for c in crops])


@app.route('/api/dashboard')
@login_required
def api_dashboard():
    uid = session['user_id']
    conn = get_db()
    stats = {
        'total_sales': conn.execute(
            'SELECT COALESCE(SUM(total_amount),0) AS value FROM sales WHERE user_id=?',
            (uid,)
        ).fetchone()['value'],
        'total_profit': conn.execute(
            'SELECT COALESCE(SUM(profit),0) AS value FROM sales WHERE user_id=?',
            (uid,)
        ).fetchone()['value'],
        'active_stock': conn.execute(
            'SELECT COUNT(*) AS value FROM stock WHERE user_id=? AND status="stored"',
            (uid,)
        ).fetchone()['value'],
        'prediction_count': conn.execute(
            'SELECT COUNT(*) AS value FROM predictions WHERE user_id=?',
            (uid,)
        ).fetchone()['value'],
        'total_expenses': conn.execute(
            'SELECT COALESCE(SUM(amount),0) AS value FROM farm_expenses WHERE user_id=?',
            (uid,)
        ).fetchone()['value'],
    }
    recent_sales = conn.execute('''
        SELECT s.id, s.quantity_kg, s.sale_price, s.total_amount, s.profit,
               s.sale_date, c.name_en, c.name_mr
        FROM sales s JOIN crops c ON s.crop_id=c.id
        WHERE s.user_id=? ORDER BY s.created_at DESC LIMIT 5
    ''', (uid,)).fetchall()
    conn.close()
    return jsonify({
        'user': dict(get_current_user()),
        'stats': {key: round(float(value or 0), 2) for key, value in stats.items()},
        'recent_sales': [dict(row) for row in recent_sales]
    })


@app.route('/api/planner', methods=['GET', 'POST'])
@login_required
def api_planner():
    uid = session['user_id']
    conn = get_db()
    if request.method == 'POST':
        data = request.get_json() or {}
        try:
            crop_id = int(data.get('crop_id') or 0)
            area = float(data.get('area_acres') or 0)
            if crop_id <= 0 or area <= 0:
                raise ValueError('Crop and positive area are required')
            conn.execute('''
                INSERT INTO farm_plans
                (user_id,crop_id,area_acres,sowing_date,expected_harvest,
                 irrigation_plan,soil_type,notes)
                VALUES (?,?,?,?,?,?,?,?)
            ''', (uid, crop_id, area, data.get('sowing_date', ''),
                  data.get('expected_harvest', ''), data.get('irrigation_plan', ''),
                  data.get('soil_type', ''), data.get('notes', '')))
            conn.commit()
        except (ValueError, TypeError) as exc:
            conn.close()
            return jsonify({'error': str(exc)}), 400
    rows = conn.execute('''
        SELECT fp.*, c.name_en, c.name_mr FROM farm_plans fp
        JOIN crops c ON fp.crop_id=c.id WHERE fp.user_id=?
        ORDER BY COALESCE(fp.expected_harvest, fp.sowing_date) ASC
    ''', (uid,)).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])


@app.route('/api/planner/expenses', methods=['GET', 'POST'])
@login_required
def api_planner_expenses():
    uid = session['user_id']
    conn = get_db()
    if request.method == 'POST':
        data = request.get_json() or {}
        try:
            amount = float(data.get('amount') or 0)
            if amount <= 0:
                raise ValueError('Amount must be greater than zero')
            plan_id = data.get('plan_id') or None
            if plan_id:
                plan_id = int(plan_id)
                owned = conn.execute(
                    'SELECT id FROM farm_plans WHERE id=? AND user_id=?',
                    (plan_id, uid)
                ).fetchone()
                if not owned:
                    raise ValueError('Invalid crop plan')
            conn.execute('''
                INSERT INTO farm_expenses
                (user_id,plan_id,category,amount,expense_date,notes)
                VALUES (?,?,?,?,?,?)
            ''', (uid, plan_id, str(data.get('category') or 'Other').strip() or 'Other',
                  amount, str(data.get('expense_date') or '').strip(),
                  str(data.get('notes') or '').strip()))
            conn.commit()
        except (ValueError, TypeError) as exc:
            conn.close()
            return jsonify({'error': str(exc)}), 400

    rows = conn.execute('''
        SELECT fe.*, c.name_en, c.name_mr
        FROM farm_expenses fe
        LEFT JOIN farm_plans fp ON fe.plan_id=fp.id
        LEFT JOIN crops c ON fp.crop_id=c.id
        WHERE fe.user_id=?
        ORDER BY COALESCE(fe.expense_date, fe.created_at) DESC
        LIMIT 50
    ''', (uid,)).fetchall()
    total = conn.execute(
        'SELECT COALESCE(SUM(amount),0) AS total FROM farm_expenses WHERE user_id=?',
        (uid,)
    ).fetchone()['total']
    conn.close()
    return jsonify({
        'expenses': [dict(row) for row in rows],
        'total': round(float(total or 0), 2)
    })


@app.route('/api/stock')
@login_required
def api_stock():
    conn = get_db()
    rows = conn.execute('''
        SELECT st.*, c.name_en, c.name_mr, c.category FROM stock st
        JOIN crops c ON st.crop_id=c.id WHERE st.user_id=?
        ORDER BY st.created_at DESC
    ''', (session['user_id'],)).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])


@app.route('/api/sales')
@login_required
def api_sales():
    conn = get_db()
    rows = conn.execute('''
        SELECT s.*, c.name_en, c.name_mr FROM sales s
        JOIN crops c ON s.crop_id=c.id WHERE s.user_id=?
        ORDER BY s.created_at DESC
    ''', (session['user_id'],)).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])


@app.route('/api/profile', methods=['GET', 'PUT'])
@login_required
def api_profile():
    uid = session['user_id']
    if request.method == 'PUT':
        data = request.get_json() or {}
        name = (data.get('name') or '').strip()
        if not name:
            return jsonify({'error': 'Name is required'}), 400
        conn = get_db()
        conn.execute('''
            UPDATE users SET name=?, village=?, district=?, lang=?
            WHERE id=?
        ''', (name, (data.get('village') or '').strip(),
              (data.get('district') or '').strip(),
              data.get('lang', 'mr'), uid))
        conn.commit()
        conn.close()
        session['user_name'] = name

    user = get_current_user()
    return jsonify(dict(user))


# ══════════════════════════════════════════════════════════════════════════════
#  PROFILE
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/profile', methods=['GET','POST'])
@login_required
def profile():
    uid = session['user_id']
    if request.method == 'POST':
        conn = get_db()
        conn.execute('''
            UPDATE users SET name=?,village=?,district=?,lang=?
            WHERE id=?
        ''', (request.form['name'], request.form.get('village',''),
              request.form.get('district',''),
              request.form.get('lang','mr'), uid))
        conn.commit()
        conn.close()
        session['user_name'] = request.form['name']
        flash('प्रोफाइल अपडेट झाली / Profile updated', 'success')
    return render_template('profile.html', user=get_current_user())


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    init_db()
    seed_price_history()
    from ai_engine import pretrain_all_models
    pretrain_all_models()
    print("=" * 60)
    print("  🌿 KrishiAdvisor AI V2")
    print("  http://127.0.0.1:5000")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)
