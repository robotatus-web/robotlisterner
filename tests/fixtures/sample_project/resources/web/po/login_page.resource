*** Settings ***
Documentation    Page Object for the Login page — web platform.

*** Variables ***
&{IOS}
...    login_btn=//XCUIElementTypeButton[@name='Login']
...    username_field=//XCUIElementTypeTextField[@name='Username']
...    password_field=//XCUIElementTypeSecureTextField[@name='Password']
...    submit_btn=//XCUIElementTypeButton[@name='Submit']

&{ANDROID}
...    login_btn=//android.widget.Button[@text='Login']
...    username_field=//android.widget.EditText[@hint='Username']
...    password_field=//android.widget.EditText[@hint='Password']

*** Keywords ***
Input Login Credentials
    [Documentation]    Enters username and password on the login page.
    [Arguments]    ${username}    ${password}
    Input Text    ${username_field}    ${username}
    Input Text    ${password_field}    ${password}

Click Login Button
    [Documentation]    Clicks the login button on the login page.
    Click Element    ${login_btn}

Verify Login Page Loaded
    [Documentation]    Verifies that the login page elements are visible.
    Wait Until Element Is Visible    ${username_field}    timeout=${TIMEOUT}
