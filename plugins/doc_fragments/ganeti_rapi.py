#!/usr/bin/python
# -*- coding: utf-8 -*-


class ModuleDocFragment(object):
    # Standard Ganeti RAPI connection parameters
    DOCUMENTATION = r"""
options:
    rapi_address:
        description:
            - The address of the Ganeti RAPI server.
        type: str
        required: true
    rapi_port:
        description:
            - The port number of the Ganeti RAPI server.
        type: int
        required: true
    rapi_username:
        description:
            - The username for authenticating with the Ganeti RAPI server.
        type: str
        required: true
    rapi_password:
        description:
            - The password for authenticating with the Ganeti RAPI server.
        type: str
        required: true
    ssl_verify:
        description:
            - Whether to verify the SSL certificate of the RAPI server.
        type: bool
        default: true
    timeout:
        description:
            - Timeout in seconds for the RAPI connection.
        type: int
        default: 5
requirements:
    - GanetiRAPIClient library
notes:
    - The GanetiRAPIClient library must be installed on the managed node.
"""
