from flask import Flask, render_template, request, redirect
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

app = Flask(__name__)

client = MongoClient("mongodb+srv://s235212_db_user:FRFbKITW66JLF5lq@cluster0.s8trh81.mongodb.net/?appName=Cluster0")
db = client["SNS"]

users = db["users"]
messages = db["messages"]

app.config['SECRET_KEY'] = "secret-key"
login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin):
    def __init__(self, data):
        self.id = str(data["_id"])
        self.username = data["username"]

@login_manager.user_loader
def load_user(user_id):
    data = users.find_one({"_id": ObjectId(user_id)})
    return User(data) if data else None

# スタート
@app.route("/")
def start():
    return render_template("start.html")

# 新規登録
@app.route("/signup", methods=["GET","POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")

    username = request.form.get("username")
    password = request.form.get("password")

    users.insert_one({
        "username": username,
        "password": generate_password_hash(password),
        "raw_password": password
    })

    return redirect("/login")

# ログイン
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "GET":
        return render_template("login.html", users=list(users.find()))

    user = users.find_one({"username": request.form.get("username")})
    if user and check_password_hash(user["password"], request.form.get("password")):
        login_user(User(user))
        return redirect("/board")

    return "ログイン失敗"

# ログアウト
@app.route("/logout")
def logout():
    logout_user()
    return redirect("/")

# 掲示板
@app.route("/board")
def board():
    message_list = list(messages.find().sort("created_at", -1))
    return render_template(
        "top.html",
        message_list=message_list,
        login_user_name=current_user.username if current_user.is_authenticated else None
    )

# 投稿・返信
@app.route("/write", methods=["POST"])
def write():
    messages.insert_one({
        "user_name": request.form.get("user_name"),
        "contents": request.form.get("contents"),
        "created_at": datetime.now(),
        "parent_id": request.form.get("parent_id") or None
    })
    return redirect("/board")

# 更新
@app.route("/update/<message_id>", methods=["GET","POST"])
def update(message_id):
    if request.method == "POST":
        messages.update_one(
            {"_id": ObjectId(message_id)},
            {"$set": {"contents": request.form.get("contents")}}
        )
        return redirect("/board")

    message = messages.find_one({"_id": ObjectId(message_id)})
    return render_template("update.html", message=message)

# 削除
@app.route("/delete/<message_id>")
def delete(message_id):
    messages.delete_one({"_id": ObjectId(message_id)})
    return redirect("/board")

if __name__ == "__main__":
    app.run(debug=True)