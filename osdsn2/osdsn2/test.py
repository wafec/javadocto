

def func(predicate, args):
    predicate(*args)


if __name__ == '__main__':
    func(lambda p: print(p), ("wallace", ))
