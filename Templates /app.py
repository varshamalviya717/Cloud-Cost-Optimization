from flask import Flask, render_template, request, redirect, url_for, session
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from flask import send_file

import mysql.connector

app = Flask(__name__)
app.secret_key = "cloud_cost_secret_key"

# MySQL Connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="MySQL@1234",
    database="cloud_cost_optimization"
)

cursor = db.cursor()

# Home Page
@app.route('/')
def home():
    return render_template('index.html')

# Register Page
@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        fullname = request.form['fullname']
        email = request.form['email']
        mobile = request.form['mobile']
        password = request.form['password']

        # Duplicate Email Check
        cursor.execute(
            "SELECT * FROM users WHERE email=%s",
            (email,)
        )

        existing_user = cursor.fetchone()

        if existing_user:
            return """
            <h3>Email already registered.</h3>
            <a href='/login'>Go to Login</a>
            """

        # Insert New User
        sql = """
        INSERT INTO users(fullname,email,mobile,password)
        VALUES(%s,%s,%s,%s)
        """

        values = (fullname, email, mobile, password)

        cursor.execute(sql, values)
        db.commit()

        return redirect(url_for('login'))

    return render_template('register.html')
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        sql = "SELECT * FROM users WHERE email=%s AND password=%s"
        values = (email, password)

        cursor.execute(sql, values)

        user = cursor.fetchone()

        if user:

            session['user'] = email

            # Save Login History
            login_datetime = datetime.now()

            sql = """
            INSERT INTO login_history(email, login_time)
            VALUES(%s,%s)
            """

            values = (email, login_datetime)

            cursor.execute(sql, values)
            db.commit()

            login_time = datetime.now().strftime("%d-%m-%Y %I:%M %p")

            sender_email = "varshamalviya717@gmail.com"
            sender_password = "lspofzwikaudnqxr"

            subject = "Successful Login"

            body = f"""
Hello,

You have successfully logged in to Cloud Cost Optimization System.

Login Time: {login_time}

Thank You.
"""

            msg = MIMEText(body)
            msg["Subject"] = subject
            msg["From"] = sender_email
            msg["To"] = email

            try:
                server = smtplib.SMTP("smtp.gmail.com", 587)
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)
                server.quit()

                print("Login Email Sent Successfully")

            except Exception as e:
                print("Email Error:", e)

            return redirect(url_for('dashboard'))

        else:
            return "Invalid Email or Password"

    return render_template('login.html')
# Dashboard Page
@app.route('/dashboard')
def dashboard():

    if 'user' not in session:
        return redirect(url_for('login'))

    # Total Datasets
    cursor.execute("SELECT COUNT(*) FROM dataset_predictions")
    total_datasets = cursor.fetchone()[0]

    # Predictions Generated
    cursor.execute("SELECT COUNT(*) FROM dataset_predictions")
    predictions_generated = cursor.fetchone()[0]

    # Cloud Providers
    cursor.execute("SELECT COUNT(DISTINCT provider) FROM dataset_predictions")
    cloud_providers = cursor.fetchone()[0]

    # Login History
    cursor.execute("SELECT COUNT(*) FROM login_history")
    login_history = cursor.fetchone()[0]

    return render_template(
        'dashboard.html',
        total_datasets=total_datasets,
        predictions_generated=predictions_generated,
        cloud_providers=cloud_providers,
        login_history=login_history
    )

# Result Page
@app.route('/result')
def result():

    provider = request.args.get('provider')
    service = request.args.get('service')
    cost = request.args.get('cost')

    return render_template(
        'result.html',
        provider=provider,
        service=service,
        cost=cost
    )

# Report Page
@app.route('/report')
def report():

    cursor.execute("""
        SELECT project_name, budget, provider, service, cost
        FROM dataset_predictions
    """)

    rows = cursor.fetchall()

    total_projects = len(rows)
    total_budget = 0
    total_savings = 0

    data = []

    for row in rows:

        project = row[0]
        budget = int(row[1])
        provider = row[2]
        service = row[3]
        cost = row[4]

        if cost == "₹500 / Month":
            savings = budget - 500

        elif cost == "₹2500 / Month":
            savings = budget - 2500

        elif cost == "₹4500 / Month":
            savings = budget - 4500

        else:
            savings = 0

        total_budget += budget
        total_savings += savings

        data.append(
            (project, budget, provider, service, cost, savings)
        )

    return render_template(
        'report.html',
        data=data,
        total_projects=total_projects,
        total_budget=total_budget,
        total_savings=total_savings
    )
@app.route('/budget_analysis')
def budget_analysis():

    cursor.execute("""
        SELECT project_name, budget, provider, service, cost
        FROM dataset_predictions
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()

    data = []

    for row in rows:

        project = row[0]
        budget = int(row[1])
        provider = row[2]
        service = row[3]
        cost = row[4]

        if cost == "₹500 / Month":
            savings = budget - 500

        elif cost == "₹2500 / Month":
            savings = budget - 2500

        elif cost == "₹4500 / Month":
            savings = budget - 4500

        else:
            savings = 0

        print("PROJECT =", project)
        print("BUDGET =", budget)
        print("COST =", repr(cost))
        print("SAVINGS =", savings)

        data.append(
    (project, budget, provider, service, cost, savings)
)

    return render_template(
        'budget_analysis.html',
        data=data
    )

# Download PDF Report
@app.route('/download_report')
def download_report():

    cursor.execute("SELECT * FROM dataset_predictions")
    data = cursor.fetchall()

    pdf_file = "Cloud_Cost_Report.pdf"

    doc = SimpleDocTemplate(pdf_file)
    styles = getSampleStyleSheet()

    content = []

    content.append(
        Paragraph("Cloud Cost Optimization Report", styles['Title'])
    )

    content.append(Spacer(1, 12))

    for row in data:

        text = f"""
        Project Name: {row[1]}<br/>
        Provider: {row[9]}<br/>
        Service: {row[10]}<br/>
        Cost: {row[11]}<br/><br/>
        """

        content.append(
            Paragraph(text, styles['Normal'])
        )

    doc.build(content)

    return send_file(
        pdf_file,
        as_attachment=True
    )

# Data Page
@app.route('/data', methods=['GET', 'POST'])
def data():

    if request.method == 'POST':

        project_name = request.form['project_name']
        application_type = request.form['application_type']
        users_count = request.form['users']
        storage_gb = request.form['storage']
        ram_gb = request.form['ram']
        cpu_cores = request.form['cpu']
        budget = int(request.form['budget'])

        print("Budget Received =", budget)

        free_tier = request.form['free_tier']

        if budget <= 1000:
            provider = "Koyeb"
            service = "Koyeb Free Tier"
            cost = "₹500 / Month"

        elif budget <= 3000:
            provider = "Google Cloud"
            service = "Compute Engine"
            cost = "₹2500 / Month"

        else:
            provider = "AWS"
            service = "EC2"
            cost = "₹4500 / Month"

        sql = """
        INSERT INTO dataset_predictions
        (
            project_name,
            application_type,
            users_count,
            storage_gb,
            ram_gb,
            cpu_cores,
            budget,
            free_tier,
            provider,
            service,
            cost
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """

        values = (
            project_name,
            application_type,
            users_count,
            storage_gb,
            ram_gb,
            cpu_cores,
            budget,
            free_tier,
            provider,
            service,
            cost
        )

        cursor.execute(sql, values)
        db.commit()

        return redirect(
            url_for(
                'result',
                provider=provider,
                service=service,
                cost=cost
            )
        )

    return render_template('data.html')
@app.route('/test')
def test():
    return "TEST ROUTE WORKING"

@app.route('/login_history')
def login_history_page():

    cursor.execute("""
        SELECT email, login_time
        FROM login_history
        ORDER BY id DESC
    """)

    data = cursor.fetchall()

    return render_template(
        'login_history.html',
        data=data
    )

@app.route('/logout')
def logout():

    session.pop('user', None)

    return redirect(url_for('login'))


if __name__ == "__main__":
    print("MySQL Connected Successfully")
    app.run(debug=True)
