# for py2app, a setup.py file to build a standalone of the Scandroid
# COMMAND LINE:
# python setup.py py2app --iconfile Scandroid.icns 
#	--dist-dir 'the Scandroid dist' --resources scandictionary.txt

from distutils.core import setup
import py2app

NAME = 'Scandroid'
VERSION = '1.1x'

plist = dict(
	CFBundleIconFile			= 'Scandroid.icns',
	CFBundleName				= NAME,
	CFBundleShortVersionString		= VERSION,
	CFBundleGetInfoString			= ' '.join([NAME, VERSION]),
	CFBundleExecutable			= NAME,
)

setup(
	data_files=[('', ['scandictionary.txt'])],
	app = [dict(script="Scandroid.py", plist=plist),]
)
