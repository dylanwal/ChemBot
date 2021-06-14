from machine import Pin, PWM
from time import sleep

pwm = PWM(Pin(15))
pwm.freq(50)


d0 = 545 * 1000
d90 = (550 + 640) * 1000
d180 = (550+640*2-10) * 1000
d270 = 2480 * 1000

d_list = [d0, d90, d180, d270]

for i in d_list:
    pwm.duty_ns(i)
    sleep(2)

pwm.duty_ns(d0)
sleep(2)

off = Pin(15, Pin.OUT)
off.value(0)




pwm.deinit()
