from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user
from app.models import User

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/", methods=["GET","POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    if request.method == "POST":
        email = request.form.get("email","").strip().lower()
        password = request.form.get("password","")
        user = User.query.filter_by(email=email, active=True).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("main.dashboard"))
        flash("Usuário ou senha inválidos.","error")
    return render_template("auth/login.html")

@auth_bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
