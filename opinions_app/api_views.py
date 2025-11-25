from flask import jsonify, request

from . import app, db
from .error_handlers import InvalidAPIUsage
from .models import Opinion
from .views import random_opinion


@app.route("/api/opinions/<int:id>/", methods=["GET"])
def get_opinion(id):
    opinion = Opinion.query.get(id)
    if opinion is not None:
        return jsonify({"opinion": opinion.to_dict()}), 200
    raise InvalidAPIUsage("В базе данных нет такого мнения", 404)


@app.route("/api/opinions/<int:id>/", methods=["PATCH"])
def update_opinion(id):
    data = request.get_json()
    if (
        "text" in data
        and Opinion.query.filter_by(text=data["text"]).first() is not None
    ):
        raise InvalidAPIUsage("Отсутствуют обязательные поля")
    # Если метод get_or_404 не найдёт указанный ID,
    # он выбросит исключение 404:
    opinion = Opinion.query.get(id)
    if opinion is not None:
        opinion.title = data.get("title", opinion.title)
        opinion.text = data.get("text", opinion.text)
        opinion.source = data.get("source", opinion.source)
        opinion.added_by = data.get("added_by", opinion.added_by)
        # Все изменения нужно сохранить в базе данных.
        # Объект opinion добавлять в сессию не нужно.
        # Этот объект получен из БД методом get_or_404() и уже хранится в сессии.
        db.session.commit()
        # При изменении объекта нужно вернуть сам объект и код 200.
        return jsonify({"opinion": opinion.to_dict()}), 200
    raise I


@app.route("/api/opinions/<int:id>/", methods=["DELETE"])
def delete_opinion(id):
    opinion = Opinion.query.get(id)
    if opinion is not None:
        db.session.delete(opinion)
        db.session.commit()
        return "", 204
    raise InvalidAPIUsage("Такого мнения не существует")


@app.route("/api/opinions/", methods=["GET"])
def get_opinions():
    opinions = Opinion.query.all()
    opinions_list = [opinion.to_dict() for opinion in opinions]
    return jsonify({"opinions": opinions_list}), 200


@app.route("/api/opinions/", methods=["POST"])
def add_opinion():
    # Получить данные из запроса в виде словаря.
    data = request.get_json()
    if "title" not in data or "text" not in data:
        raise InvalidAPIUsage("В запросе отсутствуют обязательные поля")
    # Создать новый пустой экземпляр модели.
    if Opinion.query.filter_by(text=data["text"]).first() is not None:
        raise InvalidAPIUsage("Такое мнение уже есть в базе данных")
    opinion = Opinion()
    # Наполнить экземпляр данными из запроса.
    opinion.from_dict(data)
    # Добавить новую запись в сессию.
    db.session.add(opinion)
    # Сохранить изменения.
    db.session.commit()
    return jsonify({"opinion": opinion.to_dict()}), 201


@app.route("/api/get-random-opinion/", methods=["GET"])
def get_random_opinion():
    opinion = random_opinion()
    if opinion is not None:
        return jsonify({"opinion": opinion.to_dict()}), 200
    raise InvalidAPIUsage("В базе данных нет мнений", 404)
