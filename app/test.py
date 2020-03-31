
def func_a(a):
    return "a="+a

def func_b(b):
    return "b="+b

func_list=[func_a, func_b]

def main_func(arg):
    returns = []
    for func in func_list:
        ans = func(arg)
        returns.append(ans)

    return returns


print(main_func("test"))
