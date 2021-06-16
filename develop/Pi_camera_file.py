# camera from Labists; Sensor: OV5647

from picamera import PiCamera
import time

# intialization
camera = PiCamera()

# Take picture
camera.resolution = (2592,1944) #max picture resolution: 5 MP (2592,1944)
time.sleep(2) ## allow camera warmup
camera.capture("/home/pi/Desktop/test.jpg")
print('Picture Taken')


# Taking Video
camera.resolution = (1920, 1080) #max picture resolution: 1080p (1920, 1080) 30fps; 720p  60fps; 480p 90fps
print('Video started')
camera.start_recording("/home/pi/Desktop/test_movie.h264")
time.sleep(5)
camera.stop_recording()
print('Video done')

