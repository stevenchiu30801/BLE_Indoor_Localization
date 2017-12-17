# Indoor Localization with Bluetooth Low Energy
This repository was the project in CS498WN at UIUC. The project was in callaboration with Rohan Gupta.

# Overview
We used Nordic nRF51 Development Kit board (PCA10028) v1.1.0 as our BLE module and programmed on the base of example codes `ble_app_multilink_central` and `experimental_ble_app_blinky`.

[Termite](https://www.compuphase.com/software_termite.htm) is used to display and log data. Scripts `localization1D.py` and `localization2D.py` grab data from log files and instantaneously plot RSSI values and localization map in animation.
