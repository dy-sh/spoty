from setuptools import setup, find_packages


def read_requirements():
    with open('requirements.txt') as file:
        content = file.read()
        requirements = content.split('\n')
    return requirements


setup(
    name="spoty",
    version="0.1.0",
    description="CLI tool for management of Spotify, Deezer and other music services as well as local music files.",
    author="Dmitry Savosh",
    author_email="d.savosh@gmail.com",
    url="https://github.com/dy-sh/spoty",
    packages=find_packages(),
    include_package_data=True,
    install_requires=read_requirements(),
    entry_points="""
        [console_scripts]
        spoty=spoty.cli:cli
    """
)
