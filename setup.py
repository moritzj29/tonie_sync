from setuptools import setup

setup(name='tonie_sync',
      version='0.1',
      description='Sync Spotify playlists to creative tonies. NOT associated with Boxine (tonies.de) in any way.',
      url='https://github.com/moritzj29/tonie_api',
      author='Moritz Jung',
      author_email='18733473+moritzj29@users.noreply.github.com',
      license='MIT',
      packages=['tonie_sync'],
      install_requires=[
          'tonie_api',
          'spotdl'
      ],
      zip_safe=False)