from setuptools import setup, find_packages

setup(
    name='my_new_vm',
    version='1.0',
    description='new simple VM on Python',
    author='Priymak Eugeniy KA-13',
    packages=find_packages(where='task0'),
    package_dir={'': 'task0'},
    include_package_data=True,
)
