class A:

    def __init__(self):
        self.a = False


a = A()


def change(klasa):
    klasa.a = True

print(a.a)

change(a)
print(a.a)
