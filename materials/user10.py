from person10 import Person


class User(Person):
    def __init__(self, name, user_id):
        super().__init__(name)
        self.user_id = user_id

    def print_details(self):
        super().print_details()
        print(f"user id:   {self.user_id}")
