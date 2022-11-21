import sys

def stderr(*args, **kwargs):
    """
    Acts like the print() function but outputs to stderr instead of stdout
    """
    kwargs.update(file=sys.stderr)
    print(*args, **kwargs)
