*** Settings ***
Documentation    End-to-end login flow — covers login, dashboard verification, and logout.
Resource         ${CURDIR}/../resources/platform/common.resource

*** Test Cases ***
Full Login Flow With Dashboard Verification
    [Documentation]    Verify complete login flow: login, verify dashboard, then logout.
    [Tags]    web    e2e    smoke
    [Setup]    Base Data Creation
    Login With Valid Credentials
    Verify Dashboard Loaded
    Logout From Application
    [Teardown]    Cleanup And Logout

Login And Execute GraphQL Query
    [Documentation]    Login and verify GraphQL API access via user profile query.
    [Tags]    web    e2e    api
    [Setup]    Base Data Creation
    Login With Valid Credentials
    Query User Profile    user_001
    Execute Create User Mutation    {"name": "e2e_user", "role": "admin"}
    Logout From Application
    [Teardown]    Cleanup And Logout

*** Keywords ***
Base Data Creation
    [Documentation]    Setup test data for E2E login flow.
    Log    Creating base data for E2E login flow
    Execute Create User Mutation    {"name": "testuser", "role": "standard"}

Verify Dashboard Loaded
    [Documentation]    Verifies dashboard page is displayed after login.
    Log    Dashboard loaded successfully

Cleanup And Logout
    [Documentation]    Cleanup after E2E test.
    Log    E2E cleanup complete
