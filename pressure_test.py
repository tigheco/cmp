#!/usr/bin/python3

"""
COVID Mask Project: PPE Development
Record data from pressure sensor and average readings.

Author: Tighe Costa tighe@covidmaskproject.org
Author: Will Hovik will@covidmaskproject.org
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
sampleRate = 50                             # Sample interval [ms]
loopAmount = 30/sampleRate/1E-3             # Infinite loop
loopMessage = " Press Ctrl+C to stop."

# Argument handlerss
def set_filename(arg):
    try:
        filename = str(arg)
    except:
        raise Exception("Invalid first argument \"%s\". This specifies the "
                        " name of the file the data will be saved to and needs"
                        " to be a string." % str(arg))

    # Check if file already exists to prevent overwriting data
    if path.exists(dataDirectory+filename+".csv"):
        response = str(input("File already exists with input name. Continue? Y/N: ").lower())

        if response != "y":
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
# AIN0:
#   Negative channel = single ended (199)
#   Range: +/-10.0 V (10.0)
#   Resolution index = Default (0)
#   Settling, in microseconds = Auto (0)
names = ["AIN0_NEGATIVE_CH", "AIN0_RANGE", "AIN0_RESOLUTION_INDEX", "AIN0_SETTLING_US",
         "AIN2_NEGATIVE_CH", "AIN2_RANGE", "AIN2_RESOLUTION_INDEX", "AIN2_SETTLING_US"]
aValues = [199, 10.0, 8, 0,
           199, 10.0, 10, 0]
numFrames = len(names)
ljm.eWriteNames(handle, numFrames, names, aValues)

print("\nSet configuration:")
for i in range(numFrames):
    print("    %s : %f" % (names[i], aValues[i]))

# Read AIN0 from the LabJack with eReadNames in a loop.
names = ["AIN0", "AIN2"]
numFrames = len(names)

# Record Data -----------------------------------------------------------------
print("\nStarting %.0s read loops.%s\n" % (str(loopAmount), loopMessage))

# columns: time, iteration, voltage, pressure, voltage flow rate
data = np.zeros((1, 6), dtype=np.float32)               # Data array
i = 0                                                   # Iteration counter

tStart = time.time()                                    # Start time stamp
tLast = 0                                               # Last sampling time
while True:
    try:
        # Check current time
        t = time.time() - tStart

        # At sampling rate...
        if (t - tLast) > sampleRate*1E-3:
            tLast = t
            # Read data from Labjack
            results = np.array(ljm.eReadNames(handle, numFrames, names))

            # Convert voltages to measurements
            pressure = results[0]/5.0*3.2                   # [psi]
            flowRate = results[1]/5.0*500                   # [SLPM]

            # Save data to array
            data = np.append(data, [[t, i, results[0], pressure, results[1], flowRate]], axis=0)

            # Print results to terminal
            print("t : %6.2f s, P : %2.3f psi, Q : %3.1f SLPM"
            % (t, pressure, flowRate), end='\n')

            # Increment iteration counter
            i = i + 1
            if loopAmount is not "infinite":
                if i >= loopAmount:
                    break

    except KeyboardInterrupt:
        break

    except Exception:
        import sys
        print(sys.exc_info()[1])
        break

# Cleanup and Save Data -------------------------------------------------------
# Cleanup
ljm.close(handle)

# Save data
if filename is not "discard":
    print("Writing data to {}.csv".format(filename))
    dataLabels = "Time, AIN0, Pressure, AIN2, Flow Rate"
    dataUnits = "[s], [V], [psi], [V], [SLPM]"
    header = '\n'.join([dataLabels, dataUnits])
    np.savetxt(dataDirectory+filename+".csv", data[1:, :], delimiter=',', header=header, comments='')

# Plot ------------------------------------------------------------------------
# Set up plots
fig, axs = plt.subplots(2)
axs[0].grid(True)
axs[1].grid(True)

# Plot data
axs[0].plot(data[1:,0], data[1:,3], 'g-')        # pressure
axs[1].plot(data[1:,0], data[1:,5], 'b-')        # flow rate

# Label plots
axs[0].set_title(filename)
axs[1].set_xlabel("Time [s]")
axs[0].set_ylabel("Pressure [psi]")
axs[1].set_ylabel("Flow Rate [SLPM]")

plt.tight_layout()
plt.show()

if filename is not "discard":
    print("Saving plot to {}.png".format(filename))
    plt.title(filename)
    fig.savefig(figsDirectory+filename+".png")

"""
References:
1. P531 Fill Sensing Code inc_fill_sensor.py
    author: Tighe Costa JTCosta@honeybeerobotics.com
2. LabJack Python_LJM_2019_04_03 Example dual_ain_loop.py
    https://labjack.com/support/software/examples/ljm/python
"""
