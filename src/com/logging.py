# MIT license; Copyright (c) 2022 Ondrej Sienczak

from config.sys import verbose


class Logger:
    def __init__(self, name):
        name = f'[{name.split(".")[-1]}]'
        self.name = f'{name:<16}'

    def err(self, *args, **kwargs):
        print('!!', self.name, *args, **kwargs)

    def wrn(self, *args, **kwargs):
        print('??', self.name, *args, **kwargs)

    def msg(self, *args, **kwargs):
        print('..', self.name, *args, **kwargs)

    if verbose:
        def dbg(self, *args, **kwargs):
            print('  ', self.name, *args, **kwargs)
    else:
        def dbg(self, *args, **kwargs):
            pass
