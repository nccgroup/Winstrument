import setuptools
import sys

if sys.version_info < (3,7):
    sys.exit('winstrument requires python 3.7+')

setuptools.setup(
    name="winstrument",
    version = "0.1.0",
    long_description = open('README.md','r').read(),
    long_description_content_type = 'text/markdown',
    author='George Osterweil',
    author_email='george@georgeosterweil.com',
    url='https://github.com/nccgroup/Winstrument',
    license = 'GPLv3',
    python_requires='>=3.7.0',
    install_requires = [
        "attrs==19.1.0",
        "cmd2==0.9.15",
        "colorama==0.4.1",
        "frida>=12.6.17,<13.0.0",
        "frida-tools==3.0.0",
        "pyperclip==1.7.0",
        "pyreadline==2.1",
        "pywin32==224",
        "tabulate==0.8.3",
        "toml==0.10.0",
        "wcwidth==0.1.7"
    ],
    include_package_data=True,
    packages=setuptools.find_packages(),
    entry_points = {
        'console_scripts': [
            'winstrument=winstrument.cmdline:main',
        ],
    },
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3.7",
        "Topic :: Security",
        "Topic :: System :: Operating System",
    ],
    keywords='winstrument instrumentation frida reverse engineering'
)
