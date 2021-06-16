# This class acts as an intermediary between the Main and Stepper_Motor_Class

from string import ascii_uppercase
import re
import matplotlib.pyplot as plt
import Stepper_Motor_Class
import H_Bot_Class

# generates dictionary linking letters to numbers
LETTERS = {letter: str(index) for index, letter in enumerate(ascii_uppercase, start=1)}


class FractionCollector:
    def __init__(self, layout="layout_23ml_test_tubes", x_P1=4, y_P1=4, z_P1=16, plot=False, motor=True):
        self.x_P1 = x_P1   # position of first test tube respect to 0,0,0
        self.y_P1 = y_P1   # position of first test tube respect to 0,0,0
        self.z_P1 = z_P1   # position of first test tube respect to 0,0,0
        self.x_now = self.x_P1   # current position of head
        self.y_now = self.y_P1   # current position of head
        self.z_now = self.z_P1   # current position of head
        self.layout = layout  # test tube tray layout

        # Zero motor and move to position A1
        self.motor = motor  # Enable motor control
        if self.motor:
            # Define motors
            self.z_motor = Stepper_Motor_Class.StepperMotor(13, 11, 15, step_res='full', end_stop_pin=36,
                                                            max_rotation=360)
            self.xy_motor = H_Bot_Class.HBot(37, 35, 40, 31, 29, 33, step_res='full', end_stop_pin_x=32,
                                             end_stop_pin_y=38)
            # zero and move to first position
            self.zero()
            self.move("A1")

        # for plotting
        self.plot_op = plot  # enable plotting
        if self.plot_op:
            self.x_tubes, self.y_tubes, self.z_tubes = getattr(self, self.layout)("A1", self.x_P1, self.y_P1, self.z_P1,
                                                                                  grid=True)
            self.plot()

    def zero(self):
        # move to end stops then move to first vial position
        self.z_motor.zero()   # dir tells motor which direction to spin to hit end stop
        self.xy_motor.zero()

    def move(self, tube):
        x_out, y_out, z_out = self.layout_23ml_test_tubes(tube, self.x_P1, self.y_P1, self.z_P1)
        dx = self.x_now - x_out
        dy = self.y_now - y_out
        dz = self.z_now - z_out
        self.x_now = x_out
        self.y_now = y_out
        self.z_now = z_out

        rot_1, rot_2, rot_z = self.xyz_to_deg(dx, dy, dz)

        if self.motor:
            if rot_z != 0:  # skip z if no change
                self.z_motor.rotate(rot_z)
            self.xy_motor.rotate(rot_1, rot_2)

        if self.plot:
            print("Tube: ", position, " pos: ", x_out, y_out, z_out, " cm  rot:", rot_1, rot_2, rot_z, " deg")

    @staticmethod
    def xyz_to_deg(dx, dy, dz):
        # convert delta distance in 'cm' into degree of rotation
        pitch = 0.2  # pitch of z-axis screws
        r_z_motor = 1.5/2 # radius of pulley on motor head
        r_z_screw = 3/2  # radius of pulley on screw
        r_xy = 1.5/2   # radius of pulley on motor head

        rot_z = r_z_motor/r_z_screw*dz/pitch*360
        rot_1 = 1/r_xy*(-dx+dy)*360
        rot_2 = 1/r_xy*(-dx-dy)*360

        return rot_1, rot_2, rot_z

    # Plotting stuff
    def plot(self):
        # generate initial plot
        plt.axis([0, max(self.x_tubes) + self.x_P1, 0, max(self.y_tubes) + self.y_P1])
        plt.ion()
        plt.show()
        plt.plot(self.x_tubes, self.y_tubes, 'ro')
        plt.plot(self.x_now, self.y_now, 'bo', markersize=15)
        plt.draw()
        plt.pause(0.001)

    def plot_update(self, x, y):
        # update position of fraction collector head
        plt.cla()
        plt.axis([0, max(self.x_tubes) + self.x_P1, 0, max(self.y_tubes) + self.y_P1])
        plt.plot(self.x_tubes, self.y_tubes, 'ro')
        plt.plot(x, y, 'bo', markersize=15)
        plt.arrow(self.x_now, self.y_now, x-self.x_now, y-self.y_now, width=0.05, length_includes_head=True)
        plt.pause(0.001)

    # Layouts
    def layout_23ml_test_tubes(self, tube, x_P1, y_P1, z_P1, grid=False):
        # This layout is 15 positions in the x and 12 positions in the y axis
        # x (1 to 15); y(A to L)
        # All measurements are in cm

        # Constants
        x_spacing = 2.08  # cm
        y_spacing = 2.1  # cm
        x_spots = 15  # number of tubes on tray in x directions
        y_spots = 12  # number of tubes on tray in y directions

        if not grid:
            # This chunk will return x,y,z coordinates given a "tube"

            # Convert input into usable form
            tube_list = re.findall('\d+|\D+', tube)
            pos_x = int(tube_list[1])
            pos_y = int(LETTERS[tube_list[0]])

            # checking the input vial is valid
            if len(tube_list) > 2:
                raise ValueError('Invalid tube position format. Examples: A1, B3, C6, etc.')
            if pos_x < 0 or pos_x > x_spots:
                raise ValueError('Invalid tube position. Numbers from [1,15] are accepted.')
            if pos_y < 0 or pos_y > y_spots:
                raise ValueError('Invalid tube position. Letters from [A,L] are accepted.')

            # calculating x,y,z position
            if pos_x < 8:
                x = x_P1 + x_spacing * (pos_x - 1)
            else:
                x = x_P1 + x_spacing * pos_x  # to account for gap in tray
            y = y_P1 + y_spacing * (pos_y - 1)
            z = z_P1

            if self.plot:
                self.plot_update(x, y)

            return x, y, z

        else:
            # this returns an array of all tube positions
            x = [0] * x_spots * y_spots
            y = [0] * x_spots * y_spots
            z = [0] * x_spots * y_spots
            for i in range(x_spots):
                for ii in range(y_spots):
                    if i < 8:
                        x[ii+(i-1)*y_spots] = x_P1 + x_spacing * i
                    else:
                        x[ii + (i - 1) * y_spots] = x_P1 + x_spacing * (i+1)  # to account for gap in tray

                    y[ii+(i-1)*y_spots] = y_P1 + y_spacing * ii
                    z = z_P1

            return x, y, z

##############################################################################################################
##############################################################################################################


# Run Code (plotting only right now)
if __name__ == '__main__':
    FC = FractionCollector(plot=True, motor=False)  # Turn motor to true for motor control
    print("Enter 'end' to stop.")
    try:
        while True:
            position = input("Enter test tube position (format: A1, C13, etc.):")
            if position == "end":
                break
            FC.move(position)

    finally:
        print("End of code!")
