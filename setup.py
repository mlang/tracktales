from setuptools import setup, find_packages

setup(
  name='tracktales',
  version='0.1.0',
  packages=find_packages(),
  include_package_data=True,
  install_requires=[
    'astral',
    'ffmpeg-python',
    'jinja2',
    'mutagen',
    'openai',
    'python-mpd2',
    'requests',
    'wand',
    'xdg'
  ],
  entry_points={
    'console_scripts': [
      'tracktales = tracktales.main:main',
    ]
  }
)
