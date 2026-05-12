import os
from flask import Flask, render_template, redirect, request, abort
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from sqlalchemy import desc
from werkzeug.utils import secure_filename
from flask import flash, redirect

from forms.news import NewsForm
from forms.user import RegisterForm, LoginForm
from data.news import News
from data.users import User
from data import db_session
from forms.comm import CommForm
from data.comments import Comment
from forms.edit_profile import EditProfileForm

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

# доюавление новости
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

# удаление новостей
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

# редактирование новостей
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

# лайк
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

# дЫзлайк
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

# избранное
@app.route('/favorite/<int:id>')
@login_required
def favorite_action(id):
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.id == id).first()
    if not news:
        abort(404)
    user = db_sess.query(User).filter(User.id == current_user.id).first()

    if news in user.favorited_news:
        user.favorited_news.remove(news)
    else:
        user.favorited_news.append(news)
    db_sess.commit()

    return redirect(request.referrer or '/')

# добавление комментариев
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
        return redirect(f"/comments/{id}")

    return render_template('addcomm.html', title='Добавление комментария', form=form)

# отображение новостей
@app.route('/comments/<int:id>')
def show_comments(id):
    db_sess = db_session.create_session()

    news = db_sess.query(News).filter(News.id == id).first()

    comments = db_sess.query(Comment).filter(Comment.news_id == id).all()

    return render_template('comments.html', title='Комментарии', news=news, comments=comments)

# удаление комментариев
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

# отображение новостей
@app.route("/")
def index():
    db_sess = db_session.create_session()

    search_query = request.args.get('q', '').strip()

    if current_user.is_authenticated:
        query = db_sess.query(News).filter((News.user == current_user) | (News.is_private != True))
    else:
        query = db_sess.query(News).filter(News.is_private != True)

    if search_query:
        query = query.filter(
            (News.title.like(f"%{search_query}%")) |
            (News.content.like(f"%{search_query}%"))
        )

    news = query.order_by(desc(News.created_date)).all()

    return render_template("index.html", news=news, UPLOAD_FOLDER=UPLOAD_FOLDER)

# мои посты
@app.route("/my_news/<int:user_id>")
@login_required
def my_news(user_id):
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.user_id == user_id).order_by(desc(News.created_date)).all()
    return render_template("index.html", news=news, UPLOAD_FOLDER=UPLOAD_FOLDER)

# понравившееся
@app.route("/liked")
@login_required
def liked():
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.likes.any(id=current_user.id)).order_by(desc(News.created_date)).all()
    return render_template("index.html", news=news, title="Понравившиеся посты", UPLOAD_FOLDER=UPLOAD_FOLDER)

# добавление в избранное
@app.route('/add_starred/<int:id>')
@login_required
def add_starred_news(id):
    db_sess = db_session.create_session()
    news = db_sess.query(News).get(id)
    user = db_sess.query(User).get(current_user.id)

    if not news:
        abort(404)

    if user in news.starred:
        news.starred.remove(user)
    else:
        news.starred.append(user)

    db_sess.commit()
    return redirect(request.referrer or '/')

# избранное
@app.route("/starred")
@login_required
def starred():
    db_sess = db_session.create_session()
    user = db_sess.query(User).get(current_user.id)
    news = user.starred_news

    return render_template("index.html",
                           news=news,
                           title="Избранное",
                           UPLOAD_FOLDER=UPLOAD_FOLDER)  # Вот этого не хватало

# регистрация
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
        if form.file.data:
            file = form.file.data
            filename = secure_filename(file.filename)
            # Сохраняем физически в папку
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            # Записываем имя файла в базу данных пользователю
            user.file = filename
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        login_user(user)
        return redirect('/')
    return render_template('register.html', title='Регистрация', form=form)

# логин
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

# профиль
@app.route('/profile/<int:id>')
@login_required
def profile(id):
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == id).first()
    if not user:
        abort(404)

    query = db_sess.query(News).filter(News.user_id == id)

    if not current_user.is_authenticated or current_user.id != id:
        query = query.filter(News.is_private != True)

    news = query.order_by(desc(News.created_date)).all()

    return render_template('profile.html', title=f'Профиль {user.name}', user=user, news=news)

# редактирование профиля
@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == current_user.id).first()

        if form.file.data:
            file = form.file.data
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            user.file = filename

        user.name = form.name.data
        user.email = form.email.data
        user.about = form.about.data

        db_sess.commit()
        flash('Профиль обновлен!')
        return redirect(f'/profile/{user.id}')

    elif request.method == 'GET':
        form.name.data = current_user.name
        form.email.data = current_user.email
        form.about.data = current_user.about

    return render_template('edit_profile.html', title='Редактирование профиля', form=form)


if __name__ == '__main__':
    main()
