from flask import Flask, render_template, request, redirect, url_for
from extensions import db
from models import Expense, Allocation
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expenses.db'
db.init_app(app)

@app.route('/')
def index():
    expenses = Expense.query.all()
    allocations = Allocation.query.all()
    total_amount = sum(expense.amount for expense in expenses)
    total_allocated = sum(allocation.amount for allocation in allocations)
    return render_template('index.html', expenses=expenses, allocations=allocations,
                           total_amount=total_amount, total_allocated=total_allocated)

@app.route('/add_expense', methods=['POST'])
def add_expense():
    category = request.form.get('category')
    amount = float(request.form.get('amount'))
    date = request.form.get('date')

    new_expense = Expense(category=category, amount=amount, date=date)
    db.session.add(new_expense)
    db.session.commit()

    return redirect(url_for('index'))

@app.route('/allocate_income', methods=['POST'])
def allocate_income():
    income = float(request.form.get('income'))

    Allocation.query.delete()  # Clear previous allocations

    total_percentage = 0
    for category in ['Food & Beverage', 'Rent', 'Transport', 'Relaxing']:
        percentage = float(request.form.get(f'allocation_{category.replace(" ", "_")}'))
        if 0 <= percentage <= 100:
            amount = (income * percentage) / 100
            allocation = Allocation(category=category, amount=amount)
            db.session.add(allocation)
            total_percentage += percentage

    # if total_percentage != 100:
    #     db.session.rollback()
    #     return redirect(url_for('index'))

    db.session.commit()
    return redirect(url_for('index'))

@app.route('/compare')
def compare():
    expenses = Expense.query.all()
    allocations = Allocation.query.all()
    
    # Prepare data for comparison
    monthly_data = {}
    for expense in expenses:
        year_month = expense.date[:7]  # Extract YYYY-MM
        if expense.category not in monthly_data:
            monthly_data[expense.category] = {'spent': {}, 'allocated': 0}
        if year_month not in monthly_data[expense.category]['spent']:
            monthly_data[expense.category]['spent'][year_month] = 0
        monthly_data[expense.category]['spent'][year_month] += expense.amount

    for allocation in allocations:
        if allocation.category in monthly_data:
            monthly_data[allocation.category]['allocated'] = allocation.amount

    # Generate warnings
    warnings = []
    warning_flags = {}
    for category, data in monthly_data.items():
        months = sorted(data['spent'].keys())
        for i in range(1, len(months)):
            previous_month = months[i - 1]
            current_month = months[i]
            if data['spent'][current_month] > data['spent'][previous_month]:
                warning_flags[(category, current_month)] = True

    return render_template('compare.html', comparison=monthly_data, warnings=warning_flags)

@app.route('/clear_expenses', methods=['POST'])
def clear_expenses():
    try:
        Expense.query.delete()
        db.session.commit()
        return redirect(url_for('index'))
    except:
        db.session.rollback()
        return "There was an issue deleting the expenses"

@app.route('/clear_allocations', methods=['POST'])
def clear_allocations():
    try:
        Allocation.query.delete()
        db.session.commit()
        return redirect(url_for('index'))
    except:
        db.session.rollback()
        return "There was an issue deleting the allocations"

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables
    app.run(debug=True)
