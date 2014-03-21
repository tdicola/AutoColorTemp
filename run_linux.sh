#!/bin/bash
if [ "$(id -u)" != "0" ]; then
  echo "Must be run as root with sudo!"
  exit 1
fi

echo "Temporarily disabling FTDI drivers."
modprobe -r -q ftdi_sio
modprobe -r -q usbserial
echo

python run.py $@

echo
echo "Enabling FTDI drivers again."
modprobe -q ftdi_sio
modprobe -q usbserial
