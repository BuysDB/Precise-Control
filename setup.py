from setuptools import setup
setup(
	name='preciseControl',
	version='0.01',
	author='Buys de Barbanson',
	author_email='code@buysdb.nl',
	description='Converts gamepad axis movements into button presses',
	url='https://github.com/BuysDB/PreciseControl',
	py_modules=['precisecontrol'],
	install_requires=['pygame']
)
