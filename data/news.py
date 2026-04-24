import datetime
import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase

news_likes = sqlalchemy.Table(
    'news_likes', SqlAlchemyBase.metadata,
    sqlalchemy.Column('user_id', sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id')),
    sqlalchemy.Column('news_id', sqlalchemy.Integer, sqlalchemy.ForeignKey('news.id'))
)

news_dislikes = sqlalchemy.Table(
    'news_dislikes', SqlAlchemyBase.metadata,
    sqlalchemy.Column('user_id', sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id')),
    sqlalchemy.Column('news_id', sqlalchemy.Integer, sqlalchemy.ForeignKey('news.id'))
)

news_favorites = sqlalchemy.Table(
    'news_favorites', SqlAlchemyBase.metadata,
    sqlalchemy.Column('user_id', sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id')),
    sqlalchemy.Column('news_id', sqlalchemy.Integer, sqlalchemy.ForeignKey('news.id'))
)

news_starred = sqlalchemy.Table(
    'news_stared', SqlAlchemyBase.metadata,
    sqlalchemy.Column('user_id', sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id')),
    sqlalchemy.Column('news_id', sqlalchemy.Integer, sqlalchemy.ForeignKey('news.id'))
)

class News(SqlAlchemyBase):
    __tablename__ = 'news'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    content = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    is_private = sqlalchemy.Column(sqlalchemy.Boolean, default=True)
    file = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))
    user = orm.relationship('User')
    categories = orm.relationship("Category", secondary="association", backref="news")

    likes = orm.relationship('User', secondary=news_likes, backref='liked_news')
    dislikes = orm.relationship('User', secondary=news_dislikes, backref='disliked_news')
    favorites = orm.relationship('User', secondary=news_favorites, backref='favorited_news')
    starred = orm.relationship("User",
                               secondary=news_starred,
                               backref=orm.backref("starred_news", lazy='subquery'))

