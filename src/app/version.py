# MIT license; Copyright (c) 2022 Ondrej Sienczak


class Version(tuple):
    def __init__(self, major, minor):
        super().__init__((major, minor))

    def __repr__(self):
        return f'v{self[0]}.{self[1]}'

    def __str__(self):
        return repr(self)


version = Version(1, 2)
