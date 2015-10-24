from distutils.core import setup
import py2exe

setup(
    console=['nickel.py'],
    version='0.6.47',
    description='Nickel - nem tool',
    data_files=[('', ['README.md', 'config.ini', 'icon.ico'])]
)
