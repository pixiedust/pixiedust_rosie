from setuptools import setup, find_packages
setup(name='pixiedust_rosie',
      version='0.1',
      description='Data Wrangling',
      url='https://github.com/ibm-watson-data-lab/pixiedust_rosie',
      install_requires=['pixiedust', 'rosie'],
      author='Jamie Jenning, Terry Antony, David Taieb, Raj Singh',
      author_email='',
      license='Apache 2.0',
      packages=find_packages(),
      include_package_data=False,
      zip_safe=False
     )