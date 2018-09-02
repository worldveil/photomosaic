# clear shit
find . | grep -E "(__pycache__|\.pyc|\.pyo$)" | xargs rm -rf
rm -rf .pytest_cache

# run tests
pytest