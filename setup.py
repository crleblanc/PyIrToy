from distutils.core import setup
import irtoy

setup(name='pyirtoy',
      version=irtoy.__version__,
      py_modules=['irtoy'],
      description='Python module for transmitting and receiving infrared signals from an IR Toy (firmware rev. 22 or higher)',
      license='Creative Commons Attribution ShareAlike license v3.0',
      author='Chris LeBlanc',
      author_email='crleblanc@gmail.com',
      url='https://github.com/crleblanc/PyIrToy',
      classifiers=['Intended Audience :: Developers',
                   'Operating System :: OS Independent',
                   'Topic :: Software Development']
      )
