from setuptools import setup


def read_files(files):
    data = []
    for file in files:
        with open(file) as f:
            data.append(f.read())
    return "\n".join(data)


meta = {}
with open('praetorian_ssh_proxy/version.py') as f:
    exec(f.read(), meta)

setup(
    name='praetorian-ssh-proxy',
    version=meta['__version__'],
    packages=[
        'praetorian_ssh_proxy',
    ],
    install_requires=[
        'paramiko==2.7.*',
        'peewee==3.13.*',
        'python-dotenv==0.14.*',
    ],
    url='https://github.com/zurek11/praetorian-ssh-proxy',
    license='MIT',
    author='Adam Žúrek',
    author_email='adamzurek14@gmail.com',
    description='SSH proxy server for Praetorian API',
    long_description=read_files(['README.md', 'CHANGELOG.md']),
    long_description_content_type='text/markdown',
    entry_points={
        "console_scripts": [
            'run = praetorian_ssh_proxy.run:main'
        ]
    },
    classifiers=[
        # As from https://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Topic :: Database',
        'Topic :: Internet :: Proxy Servers',
        'Topic :: Security'
    ]
)
