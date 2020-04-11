#!/usr/bin/python3

"""
P531 Europa Pneumatic
Record data from prototype fill sensor with 4x breakbeams.

Author: Tighe Costa JTCosta@honeybeerobotics.com
"""

import sys
from os import path
import time
import numpy as np
import matplotlib.pyplot as plt

from labjack import ljm

# Save File Path --------------------------------------------------------------
dataDirectory = "data/"
figsDirectory = "figs/"

# Parse Arguments -------------------------------------------------------------
# Defaults
filename = "discard"                        # Discards data
sampleRate = 10                             # Sample interval [ms]
loopAmount = "infinite"                     # Infinite loop
loopMessage = " Press Ctrl+C to stop."

# Argument handlers
def set_filename(arg):
    try:
        filename = str(arg)
    except:
        raise Exception("Invalid first argument \"%s\". This specifies the "
                        " name of the file the data will be saved to and needs"
                        " to be a string." % str(arg))

    # Check if file already exists to prevent overwriting data
    if path.exists(dataDirectory+filename+".csv"):
        response = str(input("File already exists with input name. Continue? Y/N: "))

        if response is not ("Y" and "y"):
            sys.exit()

    return filename

def set_sampleRate(arg):
    try:
        return int(arg)
    except:
        raise Exception("Invalid second argument \"%s\". This specifies the "
                        " sample rate in ms and needs to be a number."
                        % str(arg))

def set_loopAmount(arg):
    try:
        return int(arg)
    except:
        raise Exception("Invalid third argument \"%s\". This specifies how "
                        " many iterations to loop for and needs to be a number."
                        % str(arg))

# Optional first argument specifies filename to save data as csv
if len(sys.argv) > 1:
    filename = set_filename(sys.argv[1])

# Optional second argument specifies sample rate in ms
if len(sys.argv) > 2:
    sampleRate = set_sampleRate(sys.argv[2])

# Optional third argument specifies number of iterations to loop
if len(sys.argv) > 3:
    loopAmount = set_loopAmount(sys.argv[3])
    loopMessage = ""

# Configure LabJack -----------------------------------------------------------
# Open first found LabJack T7
handle = ljm.openS("T7", "ANY", "ANY")  # T7 device, Any connection, Any identifier
info = ljm.getHandleInfo(handle)
print("Opened a LabJack with Device type: %i, Connection type: %i,\n"
      "Serial number: %i, IP address: %s, Port: %i,\nMax bytes per MB: %i" %
      (info[0], info[1], info[2], ljm.numberToIP(info[3]), info[4], info[5]))

# Setup and call eWriteNames to configure AIN on the LabJack.
# AIN0, AIN1, AIN2, AIN3:
#   Negative channel = single ended (199)
#   Range: +/-10.0 V (10.0)
#   Resolution index = Default (0)
#   Settling, in microseconds = Auto (0)
names = ["AIN0_NEGATIVE_CH", "AIN0_RANGE", "AIN0_RESOLUTION_INDEX", "AIN0_SETTLING_US",
         "AIN1_NEGATIVE_CH", "AIN1_RANGE", "AIN1_RESOLUTION_INDEX", "AIN1_SETTLING_US",
         "AIN2_NEGATIVE_CH", "AIN2_RANGE", "AIN2_RESOLUTION_INDEX", "AIN2_SETTLING_US",
         "AIN3_NEGATIVE_CH", "AIN3_RANGE", "AIN3_RESOLUTION_INDEX", "AIN3_SETTLING_US"]
aValues = [199, 10.0, 0, 0,
           199, 10.0, 0, 0,
           199, 10.0, 0, 0,
           199, 10.0, 0, 0]
numFrames = len(names)
ljm.eWriteNames(handle, numFrames, names, aValues)

print("\nSet configuration:")
for i in range(numFrames):
    print("    %s : %f" % (names[i], aValues[i]))

# Read AIN0-3 from the LabJack with eReadNames in a loop.
numFrames = 4
names = ["AIN0", "AIN1", "AIN2", "AIN3"]

# Record Data -----------------------------------------------------------------
print("\nStarting %s read loops.%s\n" % (str(loopAmount), loopMessage))

intervalHandle = 1
ljm.startInterval(intervalHandle, sampleRate*1000)      # Interval timer
data = np.zeros((1, 1+numFrames), dtype=np.float32)     # Data array
i = 0                                                   # Iteration counter

tStart = time.time()                                    # Start time stamp
while True:
    try:
        # Read data from Labjack
        t = time.time() - tStart
        results = ljm.eReadNames(handle, numFrames, names)

        # Save data to array
        data = np.append(data, [[t, results[0], results[1], results[2], results[3]]], axis=0)
        if i == 0:
            print(np.average(data[-1,1:]))

        # Print results to terminal
        print("t : %f s, AIN0 : %f V, AIN1 : %f V, AIN2 : %f V, AIN3 : %f V"
        % (t, results[0], results[1], results[2], results[3]), end='\r')

        # Increment iteration counter
        i = i + 1
        if loopAmount is not "infinite":
            if i >= loopAmount:
                break

        # Wait for sample timer to roll over
        ljm.waitForNextInterval(intervalHandle)

    except KeyboardInterrupt:
        break

    except Exception:
        import sys
        print(sys.exc_info()[1])
        break

# Cleanup and Save Data -------------------------------------------------------
# Cleanup
print("\n")
print(np.average(data[-1,1:]))
ljm.cleanInterval(intervalHandle)
ljm.close(handle)

# Save data
if filename is not "discard":
    print("Writing data to {}.csv".format(filename))
    dataLabels = "Time, " + ", ".join(names)
    dataUnits = "[s], " + ", ".join(numFrames*["[V]"])
    header = '\n'.join([dataLabels, dataUnits])
    np.savetxt(filename+".csv", data[1:, :], delimiter=',', header=header, comments='')

# Plot ------------------------------------------------------------------------
fig = plt.figure()
plt.plot(data[1:,0], np.flip(data[1:,1:], 1))
plt.legend(names[::-1], loc='upper right')
plt.xlabel("Time [sec]")
plt.ylabel("Voltage [V]")
if filename is not "discard":
    plt.title(filename)
    fig.savefig(filename + ".png")

plt.show()


"""
References:
1. LabJack Python_LJM_2019_04_03 Example dual_ain_loop.py
    https://labjack.com/support/software/examples/ljm/python
2. P559 MMX Test Code read_photo_transistor.py
    author: Sherman Lam SJLam@honeybeerobotics.com
"""
