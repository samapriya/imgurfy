import setuptools
from setuptools import find_packages


def readme():
    with open('README.md') as f:
        return f.read()


setuptools.setup(
    name='imgurfy',
    version='0.0.2',
    packages=find_packages(),
    url='https://github.com/samapriya/imgurfy',
    install_requires=['logzero >= 1.5.0', 'requests == 2.27.1'],
    license='Apache 2.0',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Operating System :: OS Independent',
        'Topic :: Multimedia :: Graphics',
    ],
    author='Samapriya Roy',
    author_email='samapriya.roy@gmail.com',
    description='Simple CLI for Imgur API',
    entry_points={
        'console_scripts': [
            'imgurfy=imgurfy.imgurfy:main',
        ],
    },
)
