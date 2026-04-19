from user10 import User


class Staff(User):
    def __init__(self, name, user_id, job):
        super().__init__(name, user_id)
        self.job = job
        self.modules = []

    def print_details(self):
        super().print_details()
        print(f"job title: {self.job}")
        for module in self.modules:
            print(f" {module}")

    def attached_to(self, module):
        return module in self.modules
