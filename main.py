import os
from flask import Flask, render_template, redirect, request, abort
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from sqlalchemy import desc
from werkzeug.utils import secure_filename

from forms.news import NewsForm
from forms.user import RegisterForm, LoginForm
from data.news import News
from data.users import User
from data import db_session
from forms.comm import CommForm
from data.comments import Comment

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
UPLOAD_FOLDER = "static/uploads/"


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    user = db_sess.get(User, user_id)
    return user

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


def main():
    db_session.global_init("db/blogs.db")
    app.run(host='0.0.0.0', port=5000)


@app.route('/news', methods=['GET', 'POST'])
@login_required
def add_news():
    form = NewsForm()
    if form.validate_on_submit():
        file = form.file.data
        filename = None
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
        db_sess = db_session.create_session()
        news = News()
        news.title = form.title.data
        news.content = form.content.data
        news.file = filename
        news.is_private = form.is_private.data
        current_user.news.append(news)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/')
    return render_template('news.html', title='Добавление новости', form=form, current_file=None)


@app.route('/news_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def news_delete(id):
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.id == id, News.user == current_user).first()
    if news:
        filename = news.file
        news.likes.clear()
        news.dislikes.clear()
        db_sess.delete(news)
        db_sess.commit()

        # Проверяем, остались ли другие новости с таким же файлом
        if filename:
            other_news = db_sess.query(News).filter(News.file == filename).first()
            if not other_news:
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
    else:
        abort(404)
    return redirect('/')


@app.route('/news/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_news(id):
    form = NewsForm()
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.id == id, News.user == current_user).first()

    if not news:
        abort(404)

    if request.method == "GET":
        form.title.data = news.title
        form.content.data = news.content
        form.is_private.data = news.is_private

    if form.validate_on_submit():
        filename_old = news.file
        file = form.file.data

        news.title = form.title.data
        news.content = form.content.data
        news.is_private = form.is_private.data

        if file:
            filename_new = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename_new))
            news.file = filename_new
            db_sess.commit()

            if filename_old and filename_old != filename_new:
                other_news = db_sess.query(News).filter(News.file == filename_old).first()
                if not other_news:
                    file_path = os.path.join(UPLOAD_FOLDER, filename_old)
                    if os.path.exists(file_path):
                        os.remove(file_path)
        else:
            db_sess.commit()

        return redirect('/')
    return render_template('news.html', title='Редактирование новости', form=form, current_file=news.file)


@app.route('/like/<int:id>')
@login_required
def like_action(id):
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.id == id).first()
    if not news:
        abort(404)

    user = db_sess.query(User).filter(User.id == current_user.id).first()

    user_ids_in_likes = [u.id for u in news.likes]
    user_ids_in_dislikes = [u.id for u in news.dislikes]

    if user.id in user_ids_in_dislikes:
        news.dislikes.remove(user)

    if user.id in user_ids_in_likes:
        news.likes.remove(user)
    else:
        news.likes.append(user)

    db_sess.commit()

    return redirect(request.referrer or '/')


@app.route('/dislike/<int:id>')
@login_required
def dislike_action(id):
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.id == id).first()
    if not news:
        abort(404)
    user = db_sess.query(User).filter(User.id == current_user.id).first()

    user_ids_in_likes = [u.id for u in news.likes]
    user_ids_in_dislikes = [u.id for u in news.dislikes]


    if user.id in user_ids_in_likes:
        news.likes.remove(user)  # Удаляем из дизлайков
    if user.id in user_ids_in_dislikes:
        news.dislikes.remove(user)
    else:
        news.dislikes.append(user)  # Добавляем в лайки
    db_sess.commit()

    return redirect(request.referrer or '/')



# Добавляем <int:id> в путь
@app.route('/addcomm/<int:id>', methods=['GET', 'POST'])
def addcomm(id):
    form = CommForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()

        comment = Comment()
        comment.content = form.content.data
        comment.news_id = id
        comment.user_id = current_user.id

        db_sess.add(comment)
        db_sess.commit()
        return redirect('/')

    # Передаем форму в шаблон
    return render_template('addcomm.html', title='Добавление комментария', form=form)


@app.route('/comments/<int:id>')
def show_comments(id):
    db_sess = db_session.create_session()

    # Получаем объект новости по id
    news = db_sess.query(News).filter(News.id == id).first()

    # Получаем все комментарии к этой новости
    comments = db_sess.query(Comment).filter(Comment.news_id == id).all()

    # Передаем ОБЪЕКТ news (чтобы работал news.id в шаблоне) и список comments
    return render_template('comments.html', title='Комментарии', news=news, comments=comments)

@app.route('/delete_comment/<int:id>')
@login_required
def delete_comment(id):
    db_sess = db_session.create_session()
    comment = db_sess.query(Comment).filter(Comment.id == id,
                                            Comment.user_id == current_user.id).first()
    if comment:
        news_id = comment.news_id
        db_sess.delete(comment)
        db_sess.commit()
        return redirect(f'/comments/{news_id}')
    else:
        abort(404)



@app.route("/")
def index():
    db_sess = db_session.create_session()
    if current_user.is_authenticated:
        news = db_sess.query(News).filter((News.user == current_user) | (News.is_private != True)).order_by(desc(News.created_date)).all()
    else:
        news = db_sess.query(News).filter(News.is_private != True).order_by(desc(News.created_date)).all()
    return render_template("index.html", news=news, UPLOAD_FOLDER=UPLOAD_FOLDER)


@app.route("/my_news/<int:user_id>")
@login_required
def my_news(user_id):
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.user_id == user_id).order_by(desc(News.created_date)).all()
    return render_template("index.html", news=news, UPLOAD_FOLDER=UPLOAD_FOLDER)


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация', form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация', form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
            about=form.about.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html', message="Неправильный логин или пароль", form=form)
    return render_template('login.html', title='Авторизация', form=form)


if __name__ == '__main__':
    main()
