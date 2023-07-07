"""
https://carbon.now.sh/?bg=rgba%28255%2C255%2C255%2C1%29&t=material&wt=none&l=python&width=680&ds=true&dsyoff=20px&dsblur=68px&wc=true&wa=true&pv=56px&ph=56px&ln=true&fl=1&fm=Hack&fs=14px&lh=133%25&si=false&es=2x&wm=false&code=x1%2520%253D%25200%250Ax2%2520%253D%25200.1%250Afx1%2520%253D%2520x1**2%2520%252B%2520x1%2520-%25202%250A%250Awhile%2520abs%28fx1%29%2520%253E%25201e-6%253A%250A%2520%2520%2520%2520fx2%2520%253D%2520x2**2%2520%252B%2520x2%2520-%25202%250A%2520%2520%2520%2520xtemp%2520%253D%2520x1%250A%2520%2520%2520%2520x1%2520%253D%2520x1%2520-%2520%28x1%2520-%2520x2%29%2520*%2520fx1%2520%252F%2520%28fx1%2520-%2520fx2%29%250A%2520%2520%2520%2520x2%2520%253D%2520xtemp%250A%2520%2520%2520%2520fx1%2520%253D%2520x1%2520**%25202%2520%252B%2520x1%2520-%25202%250A%250Aprint%28x1%29%2520%2520%2523%25201.00

config
{"paddingVertical":"56px","paddingHorizontal":"49px","backgroundImage":null,"backgroundImageSelection":null,"backgroundMode":"color","backgroundColor":"rgba(255,255,255,1)","dropShadow":true,"dropShadowOffsetY":"25px","dropShadowBlurRadius":"62px","theme":"material","windowTheme":"none","language":"python","fontFamily":"Hack","fontSize":"13.5px","lineHeight":"133%","windowControls":true,"widthAdjustment":false,"lineNumbers":true,"firstLineNumber":1,"exportSize":"2x","watermark":false,"squaredImage":false,"hiddenCharacters":false,"class_name":"","width":"680","highlights":null}

python
material
white
"""

x1 = 0
x2 = 0.1
fx1 = x1**2 + x1 - 2

while abs(fx1) > 1e-6:
    fx2 = x2**2 + x2 - 2
    xtemp = x1
    x1 = x1 - (x1 - x2) * fx1 / (fx1 - fx2)
    x2 = xtemp
    fx1 = x1 ** 2 + x1 - 2

print(x1)  # 1.00


#######################################################################################################################


def secant_method(f, x1, x2):
    fx1 = f(x1)
    while abs(fx1) > 1e-6:
        fx1 = f(x1)
        fx2 = f(x2)
        xtemp = x1
        x1 = x1 - (x1 - x2) * fx1 / (fx1 - fx2)
        x2 = xtemp
    return x1


def equation(x):
    y = x**2 + x - 2
    return y


root = secant_method(equation, 0, 0.1)
print(root)  # 1.00


#######################################################################################################################

class SecantSolver:
    def __init__(self, equation: Callable, x1: int | float, x2: int | float):
        self.equation = equation
        self.x1 = x1
        self.x2 = x2

    def solve(self):
        while abs(self.equation(self.x1)) > 1e-6:
            fx1 = self.equation(self.x1)
            fx2 = self.equation(self.x2)
            xtemp = self.x1
            self.x1 = self.x1 - (self.x1 - self.x2) * fx1 / (fx1 - fx2)
            self.x2 = xtemp

        return self.x1


def equation(x: int | float):
    y = x**2 + x - 2
    return y


solver = SecantSolver(equation, 0, 0.1)
root = solver.solve()
print(root)   # 1.00

#######################################################################################################################

import time

time.sleep(0.1)

start = time.perf_counter()
root = equation(0)
end = time.perf_counter()

print("time", end-start)



