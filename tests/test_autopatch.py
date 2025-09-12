
pytest_plugins = ["pytester"]

def test_autopatcher_bare(pytester):
    # verify that even if we're using directly jubilant's temp_model, we are in fact using pytest-jubilant's functionality
    # create a temporary pytest test file
    pytester.makepyfile(
        """
        import jubilant
        import os
        os.environ["PYTESTING_PYTEST_JUBILANT"] = "1"
        
        def test_temp_model(cli_mock):
            with jubilant.temp_model():
                assert cli_mock.called
                assert cli_mock.call_args[0][0][:-1] == ['juju', 'add-model', '--no-switch']
    """
    )

    # run all tests with pytest
    result = pytester.runpytest()

    # check that all tests passed
    result.assert_outcomes(passed=1)

def test_autopatcher_flag(pytester):
    # verify that even if we're using directly jubilant's temp_model, we are in fact using pytest-jubilant's functionality
    # create a temporary pytest test file
    pytester.makepyfile(
        """
        import jubilant
        import os
        os.environ["PYTESTING_PYTEST_JUBILANT"] = "1"
        
        def test_temp_model(cli_mock):
            with jubilant.temp_model():
                assert cli_mock.called
                assert cli_mock.call_args == ['juju', 'add-model']
    """
    )

    # run all tests with pytest
    result = pytester.runpytest("-v", "--switch")

    # check that all tests passed
    result.assert_outcomes(passed=1)