%% latex
# Thermistor


## Steinhart-Hart equation
The Steinhart-Hart equation is a model that was developed at a time when computers were not ubiquitous and most mathematical calculations were done using slide rules and other mathematical aids, such as transcendental function tables. The equation was developed as a simple method for modeling thermistor temperatures easily and more precisely.

The Steinhart-Hart equation is:

1/T = A + B(lnR) + C(lnR)2 + D(lnR)3 + E(lnR)4…

Where:
T is temperature, in Kelvins (K, Kelvin = Celsius + 273.15)
R is resistance at T, in Ohms (Ω)
A, B, C, D, and E are the Steinhart-Hart coefficients that vary depending on the type of thermistor used and the range of temperature being detected.
ln is Natural Log, or Log to the Napierian base 2.71828

The terms can go on infinitely but, because the error is so small, the equation is truncated after the cubed term and the squared term is eliminated, so the standard Steinhart-Hart equation used is this:

1/T = A + B(lnR) + C(lnR)3

This equation calculates with greater precision the actual resistance of a thermistor as a function of temperature. The more narrow the temperature range, the more accurate the resistance calculation will be. Most thermistor manufacturers provide the A, B, and C coefficients for a typical temperature range.


## B or β parameter equation
NTC thermistors can also be characterised with the B (or β) parameter equation, which is essentially the Steinhart–Hart equation with


$$ \alpha =1/T_0-(1/B)ln(R_0) $$







## Reactor thermistor

NTC Thermistors: NTCLE317E4103SBA

[Data sheet](https://www.mouser.com/datasheet/2/427/ntcle317e4103sba-2953447.pdf)

PARAMETER VALUE UNIT
Resistance value at 25 °C 10K 
Tolerance on R25-value ± 2.19 %
Temperature accuracy between
25 °C and 85 °C  ± 0.5 °C
-55 °C and 150 °C ± 1.0 °C
B25/85-value 3984 K
Tolerance on B25/85-value ± 0.5 %
Operating temperature range at
zero dissipation -55 to +150 °C
Resistance value at 85 °C 1066.1 
Maximum power dissipation at 55 °C 50 mW
Min. dielectric withstanding voltage
(RMS) between leads and coating 100 V
Dissipation factor  in still air
(for information only) 0.8 mW/K
Response time (in oil) 0.3 s
Weight  0.05 g

[details](https://www.vishay.com/docs/29053/ntcappnote.pdf)