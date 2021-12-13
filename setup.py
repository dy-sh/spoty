from setuptools import setup, find_packages

def read_requirements():
    with open('requirements.txt') as file:
        content = file.read()
        requirements = content.split('\n')

    return requirements

setup(
    name="spoty",
    version="1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=read_requirements(),
    entry_points="""
        [console_scripts]
        spoty=spoty.cli:cli
    """
)