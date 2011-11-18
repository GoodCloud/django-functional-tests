import sys

def exception_string():
    import traceback
    return '\n'.join(traceback.format_exception(*sys.exc_info()))
    
def print_exception():
    print "######################## Exception #############################"
    print exception_string()
    print "################################################################"

def silence_print():
    old_printerators=[sys.stdout,sys.stderr,sys.stdin,sys.__stdout__,sys.__stderr__,sys.__stdin__][:]
    sys.stdout,sys.stderr,sys.stdin,sys.__stdout__,sys.__stderr__,sys.__stdin__=dummyStream(),dummyStream(),dummyStream(),dummyStream(),dummyStream(),dummyStream()
    return old_printerators

def unsilence_print(printerators):
    sys.stdout,sys.stderr,sys.stdin,sys.__stdout__,sys.__stderr__,sys.__stdin__=printerators


class dummyStream:
    ''' dummyStream behaves like a stream but does nothing. '''
    # via http://www.answermysearches.com/python-temporarily-disable-printing-to-console/232/
    def __init__(self): pass
    def write(self,data): pass
    def read(self,data): pass
    def flush(self): pass
    def close(self): pass

def noprint(func):
    def wrapper(*args, **kw):
        _p = silence_print()
        output = func(*args, **kw)
        unsilence_print(_p)
        return output
    return wrapper
