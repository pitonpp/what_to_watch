# what_to_watch/opinions_app.py

import csv
import os
from datetime import datetime
from random import randrange

import click
from flask import Flask, abort, flash, redirect, render_template, url_for
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, URLField
from wtforms.validators import DataRequired, Length, Optional

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite3"
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

db = SQLAlchemy(app)
migrate = Migrate(app, db)


class Opinion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    text = db.Column(db.Text, unique=True, nullable=False)
    source = db.Column(db.String(256))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    added_by = db.Column(db.String(64))


class OpinionForm(FlaskForm):
    title = StringField(
        "Введите название фильма",
        validators=[
            DataRequired(message="Обязательное поле"),
            Length(1, 128),
        ],
    )
    text = TextAreaField(
        "Напишите мнение",
        validators=[DataRequired(message="Обязательное поле")],
    )
    source = URLField(
        "Добавьте ссылку на подробный обзор фильма",
        validators=[Length(1, 256), Optional()],
    )
    submit = SubmitField("Добавить")


@app.route("/")
def index_view():
    quantity = Opinion.query.count()
    if not quantity:
        abort(500)
    offset_value = randrange(quantity)
    opinion = Opinion.query.offset(offset_value).first()
    # Вот он — возврат функции.
    return render_template("opinion.html", opinion=opinion)


@app.route("/add", methods=["GET", "POST"])
def add_opinion_view():
    form = OpinionForm()
    if form.validate_on_submit():
        text = form.text.data
        if Opinion.query.filter_by(text=text).first() is not None:
            flash("Такое мнение уже оставлено ранее!")
            return render_template("add_opinion.html", form=form)
        opinion = Opinion(
            title=form.title.data,
            text=form.text.data,
            source=form.source.data,
        )
        db.session.add(opinion)
        db.session.commit()
        return redirect(url_for("opinion_view", id=opinion.id))
    return render_template("add_opinion.html", form=form)


# Тут указывается конвертер пути для id.
@app.route("/opinions/<int:id>")
# Параметром указывается имя переменной.
def opinion_view(id):
    # Теперь можно запросить нужный объект по id...
    opinion = Opinion.query.get_or_404(id)
    # ...и передать его в шаблон (шаблон - тот же, что и для главной страницы).
    return render_template("opinion.html", opinion=opinion)


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template("500.html"), 500


@app.errorhandler(404)
def page_nof_found(error):
    return render_template("404.html"), 404


@app.cli.command("load_opinions")
def load_opinions_command():
    """Функция загрузки мнений в базу данных."""
    # Открыть файл.
    with open("opinions.csv", encoding="utf-8") as f:
        # Создать итерируемый объект, который отображает каждую строку
        # в качестве словаря с ключами из шапки файла.
        reader = csv.DictReader(f)
        # Для подсчёта строк добавить счётчик.
        counter = 0
        for row in reader:
            # Распакованный словарь использовать
            # для создания экземпляра модели Opinion.
            opinion = Opinion(**row)
            # Добавить объект в сессию и закоммитить
            db.session.add(opinion)
            db.session.commit()
            counter += 1
    click.echo(f"Загружено мнений: {counter}")


if __name__ == "__main__":
    app.run()
