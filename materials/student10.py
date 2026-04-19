from user10 import User


class Student(User):
    def __init__(self, name, user_id, programme):
        super().__init__(name, user_id)
        self.programme = programme
        self.modules = []

    def print_details(self):
        super().print_details()
        print(f"programme: {self.programme}")
        for module in self.modules:
            print(f" {module}")

    def attached_to(self, module):
        return module in self.modules
