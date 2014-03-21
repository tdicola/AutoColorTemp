#!/bin/bash
if [ "$(id -u)" != "0" ]; then
  echo "Must be run as root with sudo!"
  exit 1
fi

echo "Temporarily disabling FTDI drivers."
kextunload -b com.apple.driver.AppleUSBFTDI
kextunload /System/Library/Extensions/FTDIUSBSerialDriver.kext
echo

python run.py $@

echo
echo "Enabling FTDI drivers again."
kextload -b com.apple.driver.AppleUSBFTDI
kextload /System/Library/Extensions/FTDIUSBSerialDriver.kext
