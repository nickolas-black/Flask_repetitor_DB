from flask import Flask, render_template, request
from flask_wtf import FlaskForm
from wtforms import RadioField, StringField
from wtforms.validators import InputRequired, Length
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
CSRF_ENABLED = True
SECRET_KEY = 'b706835de79a2b4e80506f582af3676a'
app.secret_key = 'b706835de79a2b4e80506f582af3676a'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///base.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
WTF_CSRF_SECRET_KEY = 'b706835de79a2b4e80506f582af3676a'

db = SQLAlchemy(app)
migrate = Migrate(app, db)


class Teachers(db.Model):
    """ Модель преподавателей """
    __tablename__ = 'teachers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    about = db.Column(db.String, nullable=False)
    rating = db.Column(db.Float, nullable=False)
    picture = db.Column(db.String, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    lesson_time = db.Column(db.String)
    # Ссылка на поле в модели цели (One-to-Many)
    goals = db.relationship("Goals", back_populates="goal")
    # Ссылка на поле в модели рассписание (One-to-Many)
    week_day = db.relationship("TimetableTeachers", back_populates="week")


class Goals(db.Model):
    """ Модель целей занятий """
    __tablename__ = 'goals'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String, nullable=False)
    # Ссылка на модель преподавателя (One-to-Many)
    teachers_id = db.Column(db.Integer, db.ForeignKey("teachers.id"))
    goal = db.relationship("Teachers", back_populates="goals", uselist=False)

    # Ссылка на поле в модели подбора преподавателя (One-to-Many)
    search_teacher = db.relationship("SearchTeacher", back_populates="goal", uselist=False)


class TimetableTeachers(db.Model):
    """ Модель расписания преподавателей на неделю """
    __tablename__ = 'timetables'
    id = db.Column(db.Integer, primary_key=True)
    day_times = db.Column(db.String, nullable=False)
    status = db.Column(db.Boolean, nullable=False)
    # ссылка на поле id в модели преподавателя (One-to-Many)
    teachers_id = db.Column(db.Integer, db.ForeignKey("teachers.id"))
    week = db.relationship("Teachers", back_populates="week_day", uselist=False)
    # ссылка на поле id в модели booking (One-to-Many)
    booking = db.relationship("Booking", back_populates='day_times', uselist=False)


class SearchTeacher(db.Model):
    """ Модель поиска преподавателя по критериям: цели и планируемое кол-во часов занятий в неделю """
    __tablename__ = 'search_teachers'
    id = db.Column(db.Integer, primary_key=True)
    how_time = db.Column(db.String(20), nullable=False)
    client_name = db.Column(db.String(25), nullable=False)
    client_phone = db.Column(db.String(10), nullable=False)
    # Ссылка на поле в модели цели (One-to-Many)
    goal_id = db.Column(db.Integer, db.ForeignKey("goals.id"))
    goal = db.relationship("Goals", back_populates="search_teacher", uselist=False)


class Booking(db.Model):
    """ Модель для записи на пробное занятие к преподавателю """
    __tablename__ = 'booking'
    id = db.Column(db.Integer, primary_key=True)
    client_name = db.Column(db.String(25), nullable=False)
    client_phone = db.Column(db.String(10), nullable=False)
    # ссылка на поле id в модели Teachers (One-to-Many)
    timetable_id = db.Column(db.Integer, db.ForeignKey("timetables.id"))
    # ссылка на поле free и day в модели TimetableTeachers (One-to-One)
    day_times = db.relationship("TimetableTeachers", back_populates="booking", uselist=False)


def add_record(name, about, rating, price, goal, lesson_time):
    teacher = Teachers(name=name, about=about, rating=rating, price=price, goal=goal, lesson_time=lesson_time)
    db.session.add(teacher)
    db.session.commit()
    return teacher.id  # id нового преподавателя в БД


class RequestForm(FlaskForm):  # объявление класса формы для WTForms
    name = StringField('name', [InputRequired(), Length(min=2)])
    phone = StringField('phone', [InputRequired(), Length(min=6, max=12)])
    goal = RadioField("Какая цель занятий?",
                      choices=[('0', '⛱ Для путешествий'), ('1', '🏫 Для учебы'), ('2', '🏢 Для работы'),
                               ('3', '🚜 Для переезда'), ('4', '💻 Для программирования')])
    time = RadioField("Сколько времени есть?",
                      choices=[('0', '1-2 часа в неделю'), ('1', '3-5 часов в неделю'),
                               ('2', '5-7 часов в неделю'), ('3', '7-10 часов в неделю')])


# функция выполняет запрос для получения униальных целей (для учебы, работы и т.д.)
def query_goals():
    dict_id_teachers_goals = {}
    dict_goals_unique = {}
    # тут костыль ограничение на 5 уникальных целей, (исходные цели добавляются с иконками из data.json)
    # последующие новые записи будут без иконок и они тоже будут считаться уникальными.
    # Решение: Нужно переделать модель goals.
    goals_unique = db.session.query(Goals.id, Goals.key).distinct(Goals.key).limit(6)

    # цели всех преподавателей (тоже костыль, модель нужно менять)
    goals_all = db.session.query(Goals.id, Goals.teachers_id, Goals.key)

    for id, key in goals_unique.all():
        dict_goals_unique[id] = key

    for id, key, id_teacher in goals_all.all():
        dict_id_teachers_goals[id] = (str(id_teacher)) + '' + str(key)

    all_goals = [dict_goals_unique, dict_id_teachers_goals]
    return all_goals


list_goal = []
goal = db.session.query(Goals.key).distinct().limit(5)
for g in goal:
    list_goal.append(*g)



@app.route('/')  # главная
def index():
    teachers_query = db.session.query(Teachers).order_by(Teachers.rating).limit(6)
    global list_goal
    return render_template("index.html", goals=list_goal, teachers=teachers_query.all())


@app.route('/teachers/')  # все репетиторы
def teachers():
    teachers_query = db.session.query(Teachers).order_by(Teachers.rating)
    return render_template("teachers.html", goals=query_goals(), teachers=teachers_query.all())


@app.route('/goals/<goal>/')  # цель 'goal'
def goals(goal):
    teachers_query = db.session.query(Teachers).order_by(Teachers.rating)
    return render_template("goals.html", goal=goal, goals=query_goals(), all_data=all_data,
                           teachers=teachers_query.all())


@app.route('/profiles/<int:id_teacher>/')  # профиль репетитора <id учителя>
def profiles(id_teacher):
    teacher = db.session.query(Teachers).get_or_404(id_teacher)  # если id преподавателя не найден возвращаем ошибку 404
    timetable_teacher = db.session.query(TimetableTeachers).order_by(TimetableTeachers.id).limit(56)
    list_days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']

    return render_template("profiles.html", id_techer=id_teacher, timetable_teacher=timetable_teacher,
                           days=list_days, teacher=teacher)


@app.route('/request_teacher/', methods=['GET', 'POST'])  # заявка на подбор репетитора
def request_teacher():
    form = RequestForm()
    # Прием данных из формы
    if request.method == "POST" and form.validate():
        goal_choices = {'0': '⛱ Для путешествий', '1': '🏫 Для учебы', '2': '🏢 Для работы',
                        '3': '🚜 Для переезда', '4': '💻 Для программирования'}
        time_choices = {'0': '1-2 часа в неделю', '1': '3-5 часов в неделю', '2': '5-7 часов в неделю',
                        '3': '7-10 часов в неделю'}

        teacher = SearchTeacher(
            how_time=time_choices[form.time.data],
            client_name=form.name.data,
            client_phone=form.phone.data,
        )

        goal = Goals(
            key=goal_choices[form.goal.data],
            search_teacher=teacher
        )
        try:
            db.session.add(teacher)
            db.session.add(goal)
            db.session.commit()
        # Если процесс записи в БД привел к срабатыванию исключения
        except Exception:
            render_template('404.html')

        return render_template("request_done.html", username=form.name.data, userphone=form.phone.data,
                               goal=goal_choices[form.goal.data], time=time_choices[form.time.data])

    # Обработка запроса GET
    return render_template("request.html", form=form)


@app.route('/booking/<int:id_teacher>/<day>/<time>/',
           methods=['GET', 'POST'])  # здесь будет форма бронирования <id учителя>
def booking(id_teacher, day, time):
    # Прием данных из формы
    if request.method == "POST":
        # получаем даныне из формы
        client_weekday = request.form["clientWeekday"]
        client_time = request.form["clientTime"]
        teacher = request.form["clientTeacher"]
        client_name = request.form["clientName"]
        client_phone = request.form["clientPhone"]

        # записываем выбранное время репетитора
        booking_teacher = Booking(
            client_name=client_name,
            client_phone=client_phone
        )

        db.session.add(booking_teacher)
        try:
            db.session.commit()
        except:
            return render_template("404.html")

        return render_template("booking_done.html", clientName=client_name, clientPhone=client_phone,
                               time=client_time, clientTeacher=teacher, day=client_weekday)

    # Обработка запроса GET
    teacher = db.session.query(Teachers).get_or_404(id_teacher)

    return render_template("booking.html", teacher=teacher, day=day, time=time)


if __name__ == "__main__":
    app.run('0.0.0.0', debug=True)
