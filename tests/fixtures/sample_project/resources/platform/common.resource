*** Settings ***
Documentation    Root resource — imports all platform sub-resources for chain resolution.
Resource         ${CURDIR}/../web/po/login_page.resource
Resource         ${CURDIR}/../web/flow/login_flow.resource
Resource         ${CURDIR}/../be/api/graphql.resource
Resource         ${CURDIR}/../../data/GlobalVariables.resource

*** Keywords ***
Log Platform Info
    [Documentation]    Logs information about the current platform context.
    Log    Running on platform context loaded from common.resource
