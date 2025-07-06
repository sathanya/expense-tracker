from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Wallet, Transaction
from config import Config
from sqlalchemy import desc
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

import io
import base64
from collections import defaultdict

# 🤖 Open-source QA model
from transformers import pipeline
qa_pipeline = pipeline("question-answering", model="deepset/roberta-base-squad2")

# App setup
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# Login setup
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        if User.query.filter_by(email=email).first():
            flash("Email already exists")
            return redirect(url_for('signup'))

        user = User(email=email, password=password)
        db.session.add(user)
        db.session.commit()

        wallet = Wallet(balance=0.0, owner=user)
        db.session.add(wallet)
        db.session.commit()

        flash("Signup successful! Please login.")
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials")
    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    query = Transaction.query.filter_by(user_id=current_user.id)

    search = request.args.get('search')
    if search:
        query = query.filter(Transaction.description.contains(search))

    t_type = request.args.get('type')
    if t_type and t_type != "all":
        query = query.filter_by(type=t_type)

    category = request.args.get('category')
    if category and category != "all":
        query = query.filter_by(category=category)

    sort_by = request.args.get('sort_by', 'timestamp')
    order = desc if request.args.get('order') == 'desc' else lambda x: x
    query = query.order_by(order(getattr(Transaction, sort_by)))

    transactions = query.all()

    pie_chart = generate_pie_chart(transactions)
    bar_chart = generate_bar_chart(transactions)

    return render_template('dashboard.html',
                           user=current_user,
                           transactions=transactions,
                           pie_chart=pie_chart,
                           bar_chart=bar_chart)

import traceback

@app.route('/add_transaction', methods=['GET', 'POST'])
@login_required
def add_transaction():
    if request.method == 'POST':
        try:
            t_type = request.form['type']
            amount = float(request.form['amount'])
            category = request.form['category']
            description = request.form['description']

            txn = Transaction(
                type=t_type,
                amount=amount,
                category=category,
                description=description,
                user_id=current_user.id
            )

            if t_type == 'income':
                current_user.wallet.balance += amount
            else:
                current_user.wallet.balance -= amount

            db.session.add(txn)
            db.session.commit()

            flash(f"{t_type.title()} of ₹{amount} added.")
            return redirect(url_for('dashboard'))

        except Exception as e:
            print("Error adding transaction:", e)
            traceback.print_exc()
            flash("Something went wrong while adding the transaction.")
            return redirect(url_for('add_transaction'))
    
    return render_template('add_transaction.html')

@app.route('/delete_transaction/<int:txn_id>')
@login_required
def delete_transaction(txn_id):
    txn = Transaction.query.get_or_404(txn_id)
    if txn.user_id != current_user.id:
        flash("Unauthorized access.")
        return redirect(url_for('dashboard'))

    if txn.type == 'income':
        current_user.wallet.balance -= txn.amount
    else:
        current_user.wallet.balance += txn.amount

    db.session.delete(txn)
    db.session.commit()

    flash("Transaction deleted.")
    return redirect(url_for('dashboard'))

# ✅ Chatbot with QA model
@app.route('/chatbot', methods=['GET', 'POST'])
@login_required
def chatbot():
    reply = ""
    if request.method == 'POST':
        user_input = request.form['message']
        transactions = Transaction.query.filter_by(user_id=current_user.id).all()

        context = "\n".join([
            f"{t.type} - ₹{t.amount} - {t.category} - {t.description}"
            for t in transactions
        ])

        try:
            result = qa_pipeline({
                'context': context,
                'question': user_input
            })
            reply = result['answer']
        except Exception as e:
            reply = f"Error generating response: {e}"

    return render_template("chatbot.html", reply=reply)

# Charts
def generate_pie_chart(transactions):
    data = defaultdict(float)
    for txn in transactions:
        if txn.type == 'expense':
            data[txn.category] += txn.amount
    if not data:
        return None
    fig, ax = plt.subplots()
    ax.pie(data.values(), labels=data.keys(), autopct='%1.1f%%')
    ax.set_title('Expense Distribution')
    return fig_to_base64(fig)

def generate_bar_chart(transactions):
    data = defaultdict(float)
    for txn in transactions:
        if txn.type == 'expense':
            data[txn.category] += txn.amount
    if not data:
        return None
    fig, ax = plt.subplots()
    ax.bar(data.keys(), data.values())
    ax.set_title("Category-wise Expenses")
    ax.set_ylabel("Amount (₹)")
    plt.xticks(rotation=45)
    return fig_to_base64(fig)

def fig_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    buf.seek(0)
    base64_img = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return base64_img
@app.route('/analysis')
@login_required
def analysis():
    transactions = Transaction.query.filter_by(user_id=current_user.id).all()
    pie_chart = generate_pie_chart(transactions)
    bar_chart = generate_bar_chart(transactions)
    return render_template("analysis.html", pie_chart=pie_chart, bar_chart=bar_chart)

# Run app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
