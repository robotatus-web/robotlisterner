*** Settings ***
Documentation    GraphQL API mutation and query keywords.

*** Keywords ***
Execute Create User Mutation
    [Documentation]    Executes the CreateUser GraphQL mutation to create a new user.
    [Tags]    api    graphql    mutation
    [Arguments]    ${user_data}
    Log    POST ${API_BASE} mutation CreateUser with ${user_data}

Execute Update Profile Mutation
    [Documentation]    Executes the UpdateProfile GraphQL mutation.
    [Tags]    api    graphql    mutation
    [Arguments]    ${profile_data}
    Log    POST ${API_BASE} mutation UpdateProfile with ${profile_data}

Execute Delete Account Mutation
    [Documentation]    Executes the DeleteAccount GraphQL mutation. No SIT coverage.
    [Tags]    api    graphql    mutation
    [Arguments]    ${account_id}
    Log    POST ${API_BASE} mutation DeleteAccount for ${account_id}

Query User Profile
    [Documentation]    Queries user profile data via GraphQL.
    [Tags]    api    graphql    query
    [Arguments]    ${user_id}
    Log    POST ${API_BASE} query UserProfile for ${user_id}
