# run tests
pytest -v -s

# clear shit
find . | grep -E "(__pycache__|\.pyc|\.pyo$)" | xargs rm -rf
rm -rf .pytest_cache

# remove temporary plots
# rm emosaic/tests/output/*