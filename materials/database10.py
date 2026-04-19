from person10 import Person
from staff10 import Staff
from student10 import Student
from user10 import User


def readlines(filename):
    """Return contents of text file as a list of lines."""
    with open(filename) as file:
        return file.readlines()


def get_users():
    contents = readlines("_people.csv") # read the file

    # remove the first row and determine the column headers (fields)
    fields = contents.pop(0).strip().split(",")
    for i, field in enumerate(fields):
        if field == "Name":
            NAME_COLUMN = i
        elif field == "Type":
            TYPE_COLUMN = i
        elif field == "User Id":
            USER_COLUMN = i
        elif field == "Job":
            JOB__COLUMN = i
        elif field == "Programme":
            PROG_COLUMN = i
        else:
            print(f"field '{field}' not recognised")

# process the other rows to construct the user objects
    users = []
    for row in contents:
        cells = row.strip().split(",")
        name = cells[NAME_COLUMN]
        type = cells[TYPE_COLUMN]
        user_id = cells[USER_COLUMN]
        job = cells[JOB__COLUMN]
        programme = cells[PROG_COLUMN]
        if type == "Person":
            user = Person(name)
        elif type == "User":
            user = User(name, user_id)
        elif type == "Staff":
            user = Staff(name, user_id, job)
        elif type == "Student":
            user = Student(name, user_id, programme)
        else:
            print(f"user type '{type}' not recognised")
            continue
        users.append(user)

    contents = readlines("_modules.csv") # read the file

    # remove the first row and determine the column headers (fields)
    fields = contents.pop(0).strip().split(",")
    for i, field in enumerate(fields):
        if field == "User Id":
            USER_COLUMN = i
        elif field == "Module":
            MODULE_COLUMN = i
        else:
            print(f"field '{field}' not recognised")

    # process the other rows to attach the users to modules
    for row in contents:
        cells = row.strip().split(",")
        user_id = cells[USER_COLUMN]
        module = cells[MODULE_COLUMN]
        found = False
        for user in users:
            if hasattr(user, "modules"):
                if user.user_id == user_id:
                    found = True
                    user.modules.append(module)
                    break
        if not found:
            print(f"user '{user_id}' not found in users")

    return users
