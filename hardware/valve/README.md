Home made Valve:

A valve consists of:
* a manual operated valve (it can be stainless steel or plastic),
* a servo (more details below)
* a holder for servo and valve (3D printed designs can be found in hardware section)
* a coupler to connect the valve handle to the servo moving arm. (3D printed designs can be found in hardware section)

The servo is controlled by PWM (Pulse Width Modulation) with the PWM duty (or width of the pulse) determining
the position the servo.

A recommend servo is the DSSERVO DS3218MG, Control Angle 270°, 20 Kg (can be found on amazon for ~$20).
* Stall Torque (5V): 19 kg/cm (263.8oz/in) (~2 Amps)
* Stall Torque (6.8V): 21.5 kg/cm (298.5 oz/in) (~2 Amps)
* Dead band: 3 μs  -> ~0.4 deg step size
* Speed : 0.16 sec/60°(5V) / 0.14 sec/60°(6.8V)
* Operating Voltage: 4.8 ~ 6.8 DC Volts

PWM Parameters:
* PWM frequency =  50 Hz or 20 ms (typical value for most servos)
* PMW low limit (0 deg.): 0.5 ms (500 us)
* PWM high limit (270 deg.): 2.5 ms (2500 us)
** Note: Every servo (even within the same brand/type) is slightly different. So each servo values (duty time) should
        be tuned so the servo actually hits 0 deg. and 270 deg.

    angles = {
        0: int(65535/20*0.5), 1638 # 65535 bits/ 20 ms * 0.5 = 0.5 ms duty
        90: int(65535/20*1.2), 3932 #
        180: int(65535/20*1.9), 6225 #
        270: int(65535/20*2.5),  8191 # 2.5 ms duty
    }

USB control:
To run this code over USB it should be combined with the 'PICO_general_comm.py' code.

Wiring:
    **power supply**        **servo**
    GND                     black wire (!! needs both power and pico connection)
    5-6.8 V                 red wire

    **Pico**                **servo**
    Any PWM Pin             white wire
    GND                     black wire (!! needs both power and pico connection)

    **PC**                  **Pico**
    usb                     usb
