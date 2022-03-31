echo Run "pip install wheel twine" first time.
echo Update version in setup.py and hit enter to continue
pause
rm -r dist
python setup.py clean --all bdist_wheel
python setup.py sdist bdist_wheel
twine upload dist/*