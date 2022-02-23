import re
import ast
from setuptools import setup, find_packages

_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('wavegui/__init__.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))

with open('README.md', 'rb') as f:
    long_description = f.read().decode('utf-8')

packages = ['wavegui']
packages.extend(map(lambda x: 'wavegui.{}'.format(x), find_packages('wavegui')))

setup(
    name='wavegui',
    version=version,
    url='https://github.com/pyflow/wavegui/',
    license='MIT',
    author='Wei Zhuo',
    author_email='zeaphoo@qq.com',
    description='Chia network plot manager, auto plot manager',
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=packages,
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=['basepy>=0.3.4',
        'starlette>=0.13.8',
        'uvicorn[standard]>=0.12.2',
        'itsdangerous',
        'aiofiles',
        'python-multipart'
        ],
    extras_require={
        'test': [
            'pytest>=3'
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    python_requires='>=3.7',
    entry_points='''
    '''
)
