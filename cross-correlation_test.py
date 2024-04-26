import tkinter as tk
import serial
import struct
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Setup the serial port
ser = serial.Serial('COM9', baudrate=115200, bytesize=serial.EIGHTBITS, stopbits=serial.STOPBITS_ONE,
                    parity=serial.PARITY_NONE)

# Initialize the GUI
root = tk.Tk()
root.title("Zhikun Ba @Massey2024")

# Figure and Canvas for data plotting
fig1 = Figure(figsize=(5, 4), dpi=100)
ax1 = fig1.add_subplot(111)
ax1.set_title("Serial Data Plot")
ax1.set_xlabel("Sample Number")
ax1.set_ylabel("Value")
canvas1 = FigureCanvasTkAgg(fig1, master=root)
canvas1.draw()
canvas1.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

# Figure and Canvas for cross-correlation plotting
fig2 = Figure(figsize=(5, 4), dpi=100)
ax2 = fig2.add_subplot(111)
ax2.set_title("Cross-Correlation Plot")
ax2.set_xlabel("Lag")
ax2.set_ylabel("Correlation")
canvas2 = FigureCanvasTkAgg(fig2, master=root)
canvas2.draw()
canvas2.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

# Data storage for plotting
upper_data = [0]  # Initialize with zero to handle first value filtering
lower_data = [0]  # Initialize with zero to handle first value filtering
sample_number = 0

# Labels for displaying the latest data
upper_label = tk.Label(root, text="ADC2: -")
upper_label.pack()

lower_label = tk.Label(root, text="ADC1: -")
lower_label.pack()


def read_serial():
    global sample_number
    # Check if at least 4 bytes are in the buffer
    if ser.in_waiting >= 4:
        data = ser.read(4)  # Read 4 bytes from serial port

        # Proceed only if data is exactly 4 bytes long
        if len(data) == 4:
            num = struct.unpack('<I', data)[0]  # Convert bytes to an unsigned 32-bit integer (little-endian)
            upper_16 = (num >> 16) & 0xFFFF  # Extract upper 16 bits
            lower_16 = num & 0xFFFF  # Extract lower 16 bits

            # Apply filter: if data > 6000, use the previous value instead
            if upper_16 > 6000 and len(upper_data) > 0:
                upper_16 = upper_data[-1]
            if lower_16 > 6000 and len(lower_data) > 0:
                lower_16 = lower_data[-1]

            # Update GUI labels
            upper_label.config(text=f"ADC2: {upper_16}")
            lower_label.config(text=f"ADC1: {lower_16}")

            # Store data for plotting
            if sample_number < 1000:
                upper_data.append(upper_16)
                lower_data.append(lower_16)
                sample_number += 1

                # Update data plot
                ax1.clear()
                ax1.plot(upper_data, 'r-', label='ADC2')
                ax1.plot(lower_data, 'g-', label='ADC1')
                ax1.legend()
                canvas1.draw()

                # Update cross-correlation plot if both data lengths are sufficient
                if len(upper_data) > 1 and len(lower_data) > 1:
                    cross_corr = np.correlate(upper_data - np.mean(upper_data), lower_data - np.mean(lower_data),
                                              mode='full')
                    lags = np.arange(-len(upper_data) + 1, len(lower_data))
                    ax2.clear()
                    ax2.plot(lags, cross_corr, 'b-')
                    ax2.set_title("Cross-Correlation Plot")
                    ax2.set_xlabel("Lag")
                    ax2.set_ylabel("Correlation")
                    canvas2.draw()
            elif sample_number == 1000:
                # Reset sample number and data for continuous plotting without exceeding 300 samples
                sample_number = 0
                upper_data.clear()
                lower_data.clear()
        else:
            print("Incomplete data received")
    else:
        print("No data available")

    root.after(100, read_serial)  # Schedule this function to be called every 100ms


# Start the periodic read
root.after(100, read_serial)

# Start the GUI event loop
root.mainloop()
