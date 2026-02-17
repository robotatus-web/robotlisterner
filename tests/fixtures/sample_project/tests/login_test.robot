*** Settings ***
Documentation    Atomic login validation tests.
Resource         ${CURDIR}/../resources/platform/common.resource

*** Test Cases ***
Valid Login With Default Credentials
    [Documentation]    Verify that a user can log in with valid default credentials.
    [Tags]    web    smoke    login
    [Setup]    Base Data Creation
    Login With Valid Credentials
    [Teardown]    Cleanup And Logout

Invalid Login Shows Error Message
    [Documentation]    Verify that invalid credentials show an error message.
    [Tags]    web    login    negative
    [Setup]    Base Data Creation
    Login With Custom Credentials    invalid_user    wrong_pass
    [Teardown]    Cleanup And Logout

*** Keywords ***
Base Data Creation
    [Documentation]    Setup test data for login tests — creates default user.
    Log    Creating base data for login test
    Execute Create User Mutation    {"name": "testuser", "role": "standard"}

Cleanup And Logout
    [Documentation]    Cleanup after test.
    Log    Cleanup complete
