import collections
import collections.abc

# Mandatory fix for Python 3.10+ compatibility with DroneKit
collections.MutableMapping = collections.abc.MutableMapping
collections.Iterable = collections.abc.Iterable
collections.Mapping = collections.abc.Mapping
collections.Sequence = collections.abc.Sequence 

from dronekit import connect, Command,LocationGlobal,LocationGlobalRelative
import time
import math
def get_home_location(original_location, dNorth,dEast): #function derived from DroneKit examples given in documentation of library to convert NED to latitude/longitude
        earth_radius = 6378137.0
        dLat = dNorth/earth_radius
        dLon = dEast/(earth_radius*math.cos(math.pi*original_location.lat/180))

        newlat = original_location.lat + (dLat*180/math.pi)
        newlon = original_location.lon + (dLon*180/math.pi)

        if type(original_location) is LocationGlobal:
            targetlocation = LocationGlobal(newlat,newlon,original_location.alt)
        elif type(original_location) is LocationGlobalRelative:
            targetlocation=LocationGlobalRelative(newlat,newlon,original_location.alt)
        else:
            raise Exception("Invalid Location object passed")
        return targetlocation

print("Connecting to SITL...")
vehicle = connect('127.0.0.1:14550', wait_ready=True)

vehicle.mode ="GUIDED" #mode assignment
print("Arming and Takeoff...") # arm command
vehicle.armed = True
while not vehicle.armed: time.sleep(1)

vehicle.simple_takeoff(30)
while vehicle.location.global_relative_frame.alt < 28: time.sleep(1)

origin = vehicle.location.global_relative_frame


amplitude = 10.0    #assign the amplitude of the sine wave (in meters)   
freq = 0.05         #assign the frequency of the sine wave (in Hz)   
duration = 60.0     #duration of the trajectory (in seconds)
ground_speed = 3.0  #Ground speed at which vehicle should move (m/s)   
forward_speed = 0.5 #Forward speed in north (m/s)   
rate = 5.0          #Command rate   
start = time.time() 
last_north = 0.0 

while True:
    t = time.time() - start #start of trajectory
    if t > duration:
        break

    
    dEast = amplitude * math.sin(2.0 * math.pi * freq * t) #sine wave directional command
    dNorth = forward_speed * t #forwart direction command

    target = get_home_location(origin, dNorth=dNorth, dEast=dEast) #gets us the target location
    vehicle.simple_goto(target, groundspeed=ground_speed) #commands vehicle to target location

    print(f"t={t:.1f}s dNorth={dNorth:.2f} dEast={dEast:.2f} -> {target.lat:.6f},{target.lon:.6f}")
    time.sleep(1.0 / rate)

vehicle.simple_goto(get_home_location(origin, dNorth=dNorth, dEast=0), groundspeed=1.0)


