from setuptools import setup, find_packages

setup(
    name='fabcli',
    version='1.0',
    author='fangsean',
    author_email='jsen.yin@gmail.com',
    long_description=open('README.md', encoding="utf-8").read(),
    packages=find_packages(),
    include_package_data=True,
    data_files=[('', ['fabcli.ini', 'MANIFEST.in'])],
    py_modules=['fabcli'],
    description='自定义发布工具',
    install_requires=[
        'Fabric3>=1.1,<2.0',
        'Click',
    ],
    scripts=['fabcli.py','fabfile.py'],
    entry_points='''
        [console_scripts]
        fabcli=fabcli:main
    '''
)
