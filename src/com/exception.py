# MIT license; Copyright (c) 2022 Ondrej Sienczak

from sys import print_exception, exit


def print_exc(exception):
    print_exception(exception)

    with open('error.log', 'a') as f:
        f.write('\n')
        print_exception(exception, f)
