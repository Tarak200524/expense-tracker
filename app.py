from flask import Flask, render_template, request, redirect, session, url_for, jsonify
import psycopg2
import os
app = Flask(__name__)
DATABASE_URL = os.environ.get("DATABASE_URL")
app.secret_key = os.environ.get("SECRET_KEY")

def db():
    return psycopg2.connect(DATABASE_URL)

@app.route("/")
def home():
    return redirect(url_for("login"))

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        confirm = request.form["confirm_password"]

        if password != confirm:
            return "Passwords do not match"

        conn = db()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO users (name, password, mail) VALUES (%s, %s, %s)",
            (username, password, email)
        )

        conn.commit()
        cur.close()
        conn.close()

        return redirect(url_for("login"))

    return render_template("register.html")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = db()
        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM users WHERE name=%s AND password=%s",
            (username, password)
        )

        user = cur.fetchone()
        cur.close()
        conn.close()

        if user:
            session["username"] = username
            return redirect(url_for("dashboard"))
        else:
            return "Invalid credentials"

    return render_template("login.html")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "username" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        category = request.form["category"]
        amount = request.form["amount"]
        date = request.form["date"]

        conn = db()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO expenses (name, category, amount, date) VALUES (%s, %s, %s, %s)",
            (session["username"], category, amount, date)
        )

        conn.commit()
        cur.close()
        conn.close()

        return redirect(url_for("dashboard"))

    return render_template("dashboard.html")

# ---------------- DATA API ----------------
# ---------------- DATA API ----------------
@app.route("/expenses-data")
def expenses_data():
    if "username" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT category, SUM(amount)
        FROM expenses
        WHERE name=%s
        AND DATE_TRUNC('month', date) = DATE_TRUNC('month', CURRENT_DATE)
        GROUP BY category
    """, (session["username"],))

    data = cur.fetchall()

    cur.close()
    conn.close()

    result = [{"category": row[0], "total": float(row[1])} for row in data]

    return jsonify(result)

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run()
