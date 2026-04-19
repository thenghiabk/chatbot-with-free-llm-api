class Person:
    def __init__(self, name):
        self.name = name

    def print_details(self):
        print(f"name:      {self.name}")

    def attached_to(self, module):
        return False

    def send(self, message):
        print(f" '{message}' sent to {self.name}")
