from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key'  # change in production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Model: User(id, name, email, password, joined_on)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)  # NOTE: demo only; hash in real apps
    joined_on = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<User {self.id} {self.email}>"

with app.app_context():
    db.create_all()

@app.route("/")
def home():
    return redirect(url_for("list_users"))

# Read list of all users
@app.route("/users")
def list_users():
    users = User.query.order_by(User.joined_on.desc()).all()
    return render_template("users_list.html", users=users)

# Create a user via form
@app.route("/users/new", methods=["GET", "POST"])
def create_user():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("All fields (name, email, password) are required.", "danger")
            return redirect(url_for("create_user"))

        # basic duplicate check
        if User.query.filter_by(email=email).first():
            flash("Email already exists.", "warning")
            return redirect(url_for("create_user"))

        user = User(name=name, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        flash("User created successfully.", "success")
        return redirect(url_for("list_users"))

    return render_template("user_form.html", mode="create", user=None)

# Update user details
@app.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
def edit_user(user_id):
    user = User.query.get_or_404(user_id)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email:
            flash("Name and email are required.", "danger")
            return redirect(url_for("edit_user", user_id=user.id))

        # enforce unique email (excluding self)
        existing = User.query.filter(User.email == email, User.id != user.id).first()
        if existing:
            flash("Another user already uses that email.", "warning")
            return redirect(url_for("edit_user", user_id=user.id))

        user.name = name
        user.email = email
        if password:  # change only if provided
            user.password = password
        db.session.commit()
        flash("User updated successfully.", "success")
        return redirect(url_for("list_users"))

    return render_template("user_form.html", mode="edit", user=user)

# Delete user record
@app.route("/users/<int:user_id>/delete", methods=["POST"])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash("User deleted successfully.", "info")
    return redirect(url_for("list_users"))

if __name__ == "__main__":
    # create 'instance' dir if running in some hosts; sqlite file lives alongside app by config above
    os.makedirs("instance", exist_ok=True)
    app.run(debug=True)
