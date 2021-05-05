from setuptools import setup


with open("README.md", "r") as fh:
    long_description = fh.read()


setup(
    name='windsaloft',
    version='0.0.2',
    description='Convert U/V raster to streamlines (geojson)',
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords='map weather geojson gis gfs streamline',
    url='https://github.com/olehz/windsaloft',
    author='Oleh Zamkovyi',
    author_email='oleh.zam@gmail.com',
    license='MIT',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3'
    ],
    packages=['windsaloft'],
    test_suite='tests',
    include_package_data=False,
    zip_safe=False,
    install_requires=[
        'geojson'
    ],
    extras_require={
        'test': ['numpy', 'pytest'],
    },
)