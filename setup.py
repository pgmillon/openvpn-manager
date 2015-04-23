import codecs
from setuptools import find_packages, setup

setup(
    name='openvpn-manager',
    version='1.0.0.dev4',
    license='MIT',
    author='Pierre-Gildas MILLON',
    author_email='pg.millon@gmail.com',
    description='A simple OpenVPN Manager',
    long_description=codecs.open('README.rst', encoding='utf-8').read(),
    url='https://github.com/pgmillon/openvpn-manager',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: System :: Networking',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7'
    ],
    keywords='openvpn manager',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'flask',
        'flask_jsontools',
        'flask_restless',
        'flask_sqlalchemy',
        'psutil',
        'tornado',
        'requests'
    ]
)