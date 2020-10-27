import json
from app import Teachers, Goals, TimetableTeachers, db


def import_json_data():
    with open('data.json', 'r') as r:
        all_data = json.load(r)
        for teacher in all_data[1]:
            teacher = Teachers(
                name=teacher['name'],
                about=teacher['about'],
                rating=teacher['rating'],
                picture=teacher['picture'],
                price=teacher['price'],
                lesson_time='8:00')
            db.session.add(t)
            for goal in teacher['goals']:
                db.session.add(Goals(key=goal, goal=teacher))
            for day in teacher['free']:
                for times, status in teacher['free'][day].items():
                    db.session.add(
                        TimetableTeachers(
                            day_times=str(times),
                            status=status,
                            week=teacher
                        )
                    )
    db.session.commit()
    r.close()


if __name__ == '__main__':
    import_json_data()
