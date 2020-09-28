from printy import printy


def success(msg):
    printy(msg, 'nB')


def info(msg):
    printy(msg)


def warning(msg):
    printy(msg, 'yB')


def error(msg):
    printy(msg, 'rB')
