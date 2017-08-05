#!/usr/bin/env python

from setuptools import setup

with open('requirements.txt') as f:
    install_reqs = f.read().splitlines()



setup(name='hrate',
      version='0.0.1',
      description='TBD',
      url='https://github.com/ppuggioni/hrate',
      author='Paolo Puggioni',
      author_email='p.paolo321@gmail.com',
      license='MIT',
      packages=['hrate'],
      install_requires=install_reqs,
      zip_safe=False)