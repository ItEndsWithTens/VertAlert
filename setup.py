from distutils.core import setup

setup(
    name='vertalert',
    version='1.0.0',
    description='Find, display, and optionally round floating point plane '
                'coordinates in Source engine VMF files.',
    author='Robert Martens',
    author_email='robert.martens@gmail.com',
    url='http://www.gyroshot.com/vertalert.htm',
    license = 'MIT',
    platforms='MacOS X, Windows, Linux',
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developer',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Topic :: Games/Entertainment',
        'Topic :: Utilities'
    ],
    py_modules=['vertalert']
)
