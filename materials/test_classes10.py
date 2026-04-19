from person10 import Person
from staff10 import Staff
from student10 import Student
from user10 import User


def check(user, capsys):
    assert user.name == "Dummy Name"
    if hasattr(user, "user_id"):
        assert user.user_id == "id001"
    if hasattr(user, "job"):
        assert user.job == "Lecturer"
    elif hasattr(user, "programme"):
        assert user.programme == "BSc"
    if hasattr(user, "modules"):
        assert len(user.modules) == 0
        user.modules.append("XY1234")
        assert len(user.modules) == 1
        assert user.modules[0] == "XY1234"

    with capsys.disabled():
        print()
        print(f"tested {user.__class__.__name__} successfully")


def test_classes(capsys):
    person = Person("Dummy Name")
    user = User("Dummy Name", "id001")
    staff = Staff("Dummy Name", "id001", "Lecturer")
    student = Student("Dummy Name", "id001", "BSc")
    users = [person, user, staff, student]
    for user in users:
        check(user, capsys)
