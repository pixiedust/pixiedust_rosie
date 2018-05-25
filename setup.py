from setuptools import setup, find_packages
setup(name='pixiedust_rosie',
      version='0.3',
      description='Data Wrangling',
      url='https://github.com/ibm-watson-data-lab/pixiedust_rosie',
      install_requires=['pixiedust', 'rosie'],
      author='Jamie Jenning, Terry Antony, David Taieb, Raj Singh',
      author_email='info@rosie-lang.org,terryantony122@gmail.com,david_taieb@us.ibm.com',
      license='Apache 2.0',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False
     )