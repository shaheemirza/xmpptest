from distutils.core import setup
from setuptools import setup, find_packages

setup( name='xmpptest',
    version='0.1',
    description='Xmpp test tool',
    author='Stas Kridzanovskiy',
    author_email='slaviann@gmail.com',
    packages=find_packages(),
      install_requires=[
          'sleekxmpp',
          'python-dateutil',
      ],
      scripts=['bin/xmpptest'],

    )
