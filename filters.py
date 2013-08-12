

def predicate(value):
    sp = value.rfind('#') != -1 and '#' or '/'
    return value.rsplit(sp, 1)[1]


def strand(value, orientation):
    if orientation == 'both':
        orientation = predicate(value['orientation'].value)

    if orientation == 'forward':
        return '+'
    elif orientation == 'reverse':
        return '-'
    else:
        return '.'

