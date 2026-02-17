*** Settings ***
Documentation    Business-level login flow keywords.
Resource         ${CURDIR}/../po/login_page.resource

*** Keywords ***
Login With Valid Credentials
    [Documentation]    Performs a complete login using valid default credentials.
    [Tags]    web    smoke
    Verify Login Page Loaded
    Input Login Credentials    ${DEFAULT_USER}    ${DEFAULT_PASSWORD}
    Click Login Button

Login With Custom Credentials
    [Documentation]    Performs login with provided custom credentials.
    [Arguments]    ${username}    ${password}
    Verify Login Page Loaded
    Input Login Credentials    ${username}    ${password}
    Click Login Button

Logout From Application
    [Documentation]    Logs out the current user from the application.
    [Tags]    web
    Click Element    id=menu-button
    Click Element    id=logout-link
    Wait Until Element Is Visible    ${username_field}    timeout=${TIMEOUT}
