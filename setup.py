from setuptools import setup, find_packages


def read_requirements():
    with open('requirements.txt') as file:
        content = file.read()
        requirements = content.split('\n')
    return requirements

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="spoty",
    version="0.1.0",
    description="CLI tool for management of Spotify, Deezer and other music services as well as local music files.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Dmitry Savosh",
    author_email="d.savosh@gmail.com",
    url="https://github.com/dy-sh/spoty",
    license="MIT",
    packages=find_packages(),
    include_package_data=True,
    install_requires=read_requirements(),
    python_requires='>=3.7',
    keywords=["music", "audio", "spotify", "deezer"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Environment :: Console",
        "Topic :: Multimedia :: Sound/Audio",
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3'
    ],
    entry_points="""
        [console_scripts]
        spoty=spoty.cli:cli
    """
)
