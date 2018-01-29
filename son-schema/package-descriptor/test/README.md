# Package Descriptor Tests

Contains all the tests that are executed automatically by Jenkins as well as the corresponding resources.

### Test Configuration

By default, the corresponding Jenkins job is looking for 'test_*.sh' files in test-directories of the repository. All the tests found are executed automatically. The tests are called without any parameter.

In order to add an additional test, one just have to upload a Bash script. Tests are considered successful if they exit with exit code 0.
