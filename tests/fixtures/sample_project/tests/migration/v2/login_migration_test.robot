*** Settings ***
Documentation    Migration test for v2 login flow — validates backward compatibility.
Resource         ${CURDIR}/../../../resources/platform/common.resource

*** Test Cases ***
V2 Login With Default Credentials
    [Documentation]    Verify that a user can log in with valid default credentials after v2 migration.
    [Tags]    web    migration    login
    [Setup]    Base Data Creation
    Login With Valid Credentials
    [Teardown]    Cleanup And Logout

*** Keywords ***
Base Data Creation
    [Documentation]    Setup test data for login migration test — creates default user.
    Log    Creating base data for v2 login migration test
    Execute Create User Mutation    {"name": "testuser", "role": "standard"}

Cleanup And Logout
    [Documentation]    Cleanup after migration test.
    Log    Migration cleanup complete
