from random import choice, random
from flask import flash
from flask import Flask, render_template, redirect, request
from flask_login import login_required
from flask_login import logout_user
from flask_login import LoginManager, current_user, login_user
from flask_migrate import Migrate
from flask import jsonify
from datetime import datetime

import os  # 環境変数を使うために追加

app = Flask(__name__)

from models import Task, User, db

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////tmp/app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "deadbeef"
db.init_app(app)
with app.app_context():
    db.create_all()

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

# --- 以下、ルート定義（register, login 等）は変更なし ---
# (中略)

if __name__ == "__main__":
    # Renderは環境変数 PORT を指定してくるため、それに合わせます
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html", title="ユーザ登録")
    else:
        if (
            request.form["id"] == ""
            or request.form["password"] == ""
            or request.form["lastname"] == ""
            or request.form["firstname"] == ""
        ):
            flash("入力されていない項目があります")
            return render_template("register.html", title="ユーザ登録")
        if User.query.get(request.form["id"]) is not None:
            flash("ユーザを登録できません")
            return render_template("register.html", title="ユーザ登録")

        user = User(  # 　フォームに入力された内容でユーザを用意
            id=request.form["id"],
            password=request.form["password"],
            lastname=request.form["lastname"],
            firstname=request.form["firstname"],
        )
        db.session.add(user)
        db.session.commit()
        return redirect("/")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect("/")

    if request.method == "GET":
        return render_template("login.html", title="🔓Login")
    else:
        user = User.query.get(request.form["id"])
        if user is not None and user.verify_password(request.form["password"]):
            login_user(user)
            return redirect("/")
        else:
            flash("ユーザIDかパスワードが誤っています")
            return redirect("/login")


@app.route("/logout")
def logout():
    logout_user()
    return redirect("/login")


@app.route("/")  # / にアクセスされたときの処理
@login_required
def index():  # 　　を担当する関数index()
    my_tasks = Task.query.filter_by(user=current_user)
    shared_tasks = Task.query.filter((Task.user != current_user) & Task.is_shared)
    return render_template(
        "index.html", title="ホーム", my_tasks=my_tasks, shared_tasks=shared_tasks
    )


@app.route("/create", methods=["POST"])
@login_required
def create():
    # 文字列を Python の日時オブジェクトに変換
    deadline_str = request.form["deadline"]
    try:
        # "2026-03-17T01:37" のような形式を想定
        deadline_dt = datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M')
    except ValueError:
        # 形式が違う場合の予備設定
        deadline_dt = datetime.now()

    task = Task(
        user_id=current_user.id,
        name=request.form["name"],
        deadline=deadline_dt, # 変換したオブジェクトを渡す
        is_shared=request.form.get("is_shared") is not None,
    )
    db.session.add(task)
    db.session.commit()
    return redirect("/")



@app.route("/update/<int:id>", methods=["GET", "POST"])
@login_required
def update(id):
    if current_user.id is None:
        flash("ログインしていません。再ログインしてください。")
        return redirect("/login")
    task = Task.query.get(id)
    if task is None or task.user != current_user:
        flash("存在しないタスクです")
        return redirect("/")

    if request.method == "GET":
        return render_template("update.html", title="更新", task=task)
    else:
        task.name = request.form["name"]
        task.deadline = request.form["deadline"]
        task.is_shared = request.form.get("is_shared") is not None
        task.user_id = current_user.id
        if task.user_id is None:
            flash("タスクにユーザーIDが設定されていません")
            return redirect("/")
        db.session.commit()
        return redirect("/")


@app.route("/delete/<int:id>", methods=["GET", "POST"])
@login_required
def delete(id):
    task = Task.query.get(id)
    if task is None or task.user != current_user:
        flash("存在しないタスクです")
        return redirect("/")

    if request.method == "GET":
        return render_template("delete.html", title="削除", task=task)
    else:
        db.session.delete(task)
        db.session.commit()
        return redirect("/")


@app.route("/delete_account/<user_id>", methods=["GET", "POST"])
@login_required
def delete_account(user_id):
    user = User.query.get(user_id)
    if user is None:
        flash("存在しないアカウントです")
        return redirect("/")

    if request.method == "GET":
        return render_template("delete_account.html", title="アカウント削除", user=user)
    if user.id == current_user.id:
        Task.query.filter_by(user_id=user.id).delete()
        # そのアカウントの持つタスクも同時に消去

    db.session.delete(user)
    db.session.commit()
    logout_user()
    flash("アカウントが削除されました")
    return redirect("/login")


@app.route("/rand")
def rand():
    r = random()
    if r < 0.3:
        x = "smaller"
    elif r <= 0.7:
        x = "medium"
    else:
        x = "larger"
    return f"{r=:.3f} {x}"


@app.route("/template")
def template():
    return render_template("template.html", greeting="hello", title="あいさつ")


@app.route("/template_list")
def template_list():
    students = []  # 学生番号を入れるリスト
    for n in range(1, 101):  # studentsに2xG2001~100を追加
        students.append(f"2xG2{n:03d}")
    return render_template(
        "template_list.html", students=students, title="学生番号リスト"
    )


@app.route("/template_dict")
def template_dict():
    students = {}
    for n in range(1, 101):
        students[f"2xG2{n:03d}"] = choice(["A", "B", "C"])

    return render_template(
        "template_dict.html",
        classes=["A", "C"],
        students=students,
        title="学生ごとのクラス分け",
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
