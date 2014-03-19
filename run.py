from __future__ import print_function
import argparse
import logging
import platform
import time

import AutoColorTemp


log = logging.getLogger('main')
	

if __name__ == '__main__':
	print('Automatic Monitor Color Temperature Adjustment')
	print('Copyright 2014 Tony DiCola (tony@tonydicola.com)')
	print()

	# Define command line argument parser and parse arguments.
	parser = argparse.ArgumentParser(description='Automatically adjust display monitor color temperature to match temperature measured from sensor hardware.')
	parser.add_argument('-v,', '--verbose', action='store_true', help='display verbose logging information')
	action = parser.add_mutually_exclusive_group(required=True)
	action.add_argument('-a', '--arduino', nargs=1, metavar='PORT', help='use Arduino at provided serial port')
	action.add_argument('-f', '--ftdi', action='store_true', help='use FT232H or compatible device')
	parser.add_argument('-d', '--delay', nargs=1, default=[10], metavar='SECONDS', help='amount of seconds to wait between updates.  Default is 10 seconds.')
	parser.add_argument('-g', '--gamma', nargs=3, default=None, metavar='VALUE', help='override gamma to specified RGB values')
	args = parser.parse_args()

	# Initialize logging.
	logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING)

	# Initialize hardware color sensor connection.
	hardware = None
	if args.ftdi:
		log.info('Using FT232H compatible hardware.')
		import FT232Hardware
		hardware = FT232Hardware.FT232Hardware()
	else:
		port = args.arduino[0]
		log.info('Using Arduino hardware at port: {0}'.format(port))
		import ArduinoHardware
		hardware = ArduinoHardware.ArduinoHardware(port)

	# Initialize platform-specific gamma adjustment.
	gamma = None
	sys = platform.system()
	log.info('Detected system as: {0}'.format(sys))
	if sys == 'Darwin':
		import MacOSXGamma
		gamma = MacOSXGamma.MacOSXGamma()
	elif sys == 'Linux':
		import X11Gamma
		gamma = X11Gamma.X11Gamma()
	elif sys == 'Windows':
		pass
	else:
		raise RuntimeError('Could not find gamma adjustment for platform: {0}'.format(sys))

	# Override monitor gamma if specified in arguments.
	if args.gamma is not None:
		gamma_r, gamma_g, gamma_b = args.gamma[0:3]
		log.info('Using gamma override of: red={0} green={1} blue={2}'.format(gamma_r, gamma_g, gamma_b))
		gamma.set_gamma((gamma_r, gamma_g, gamma_b))

	# Initialize color temperature adjust logic.
	main = AutoColorTemp.AutoColorTemp(hardware, gamma)

	# Set delay between updates.
	delay = float(args.delay[0])
	print('Updating color temperature every {0} seconds.'.format(delay))

	# Main loop to update color temperature.
	print('Press Ctrl-C to quit.')
	try:
		while True:
			main.update()
			time.sleep(delay)
	except KeyboardInterrupt:
		log.info('Received keyboard interrupt, shutting down.')
	except Exception as e:
		log.error(str(e))
	finally:
		main.close()
