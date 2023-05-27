import sys
import select
import machine


# Set up the onboard LED
led = machine.Pin(25, machine.Pin.OUT)

# Set up the poll object
poll_obj = select.poll()
poll_obj.register(sys.stdin, select.POLLIN)

# Loop indefinitely
while True:
    # Wait for input on stdin
    poll_results = poll_obj.poll(1)
    if poll_results:
        # Read the data from stdin
        data = sys.stdin.readline().strip()
        if data[:5] == "burst":
            i = 0
            for i in range(int(data[5:])):
                print(i)
            print("end")
        else:
            # Write the data to the input file
            print("data: ", data)
    else:
        # Blink the LED
        led.toggle()

"""   
    2.5489817000052426   1176.9405798377563
    read:  2.1958816998667317
    write:  0.34808459946361836
"""

"""


import select
import sys
import machine


def main():
    initialization()
    main_loop()


def initialization():
    # set all pins to low right away
    for i in range(28):
        machine.Pin(i, machine.Pin.OUT).value(0)

    # Turn LED on
    machine.Pin(25, machine.Pin.OUT).value(1)


def main_loop():
    # main loop (infinite loop)
    i = 0
    while True:
        while sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            # read in message (till it sees '\r')
            message = sys.stdin.readline()

            ### Do stuff ###
            # Reply to poll
            if message[0] == "a":
                print(i)
                i += 1
            
    
if __name__ == "__main__":
    main()

12.394042400002945   806.8392601269157
read:  11.278688497724943
write:  1.0693300979910418
"""







