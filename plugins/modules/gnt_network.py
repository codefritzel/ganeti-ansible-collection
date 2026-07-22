#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
from client.models.network import NewNetwork
from client.utils import dataclass_to_dict

try:
    from ansible_collections.codefritzel.ganeti.plugins.module_utils.client_wrapper import (
        ClientWrapper,
        get_api_argument_spec,
        get_poll_argument_spec,
    )
    from ansible_collections.codefritzel.ganeti.plugins.module_utils.utils import (
        dict_diff,
    )
except ImportError:
    from plugins.module_utils.client_wrapper import (
        ClientWrapper,
        get_api_argument_spec,
        get_poll_argument_spec,
    )  # only for tests
    from plugins.module_utils.utils import dict_diff


DOCUMENTATION = r"""
---
module: gnt_network
short_description: Manage Ganeti networks
description:
    - Manage Ganeti networks on a Ganeti cluster via RAPI.
    - Supports creating, modifying, and deleting networks.
    - Existing networks are compared against the requested parameters and modified only when needed.
version_added: "0.0.1"
extends_documentation_fragment:
    - codefritzel.ganeti.ganeti_rapi
    - codefritzel.ganeti.ganeti_job_poll

options:
    network_name:
        description:
            - Name of the Ganeti network to manage.
        type: str
        required: true

    state:
        description:
            - Desired state of the network.
            - C(present) - Ensure the network exists and matches the requested parameters.
            - C(absent) - Remove the network.
        type: str
        choices: ['present', 'absent']
        default: present

    network:
        description:
            - IPv4 network address in CIDR notation.
            - Used for network creation and modification.
            - Example is C(10.0.0.0/24).
        type: str
        required: false

    gateway:
        description:
            - IPv4 gateway for the network.
            - Used for network creation and modification.
        type: str
        required: false

    network6:
        description:
            - IPv6 network address in CIDR notation.
            - Used for network creation and modification.
            - Example is C(2001:db8::/64).
        type: str
        required: false

    gateway6:
        description:
            - IPv6 gateway for the network.
            - Used for network creation and modification.
        type: str
        required: false

    mac_prefix:
        description:
            - MAC prefix to assign to instances attached to this network.
            - Used for network creation and modification.
        type: str
        required: false
"""

EXAMPLES = r"""
---
# Create a new network
- name: Create a Ganeti network
    codefritzel.ganeti.gnt_network:
        rapi_address: "ganeti-cluster"
        rapi_port: 5080
        rapi_username: "admin"
        rapi_password: "secret"
        ssl_verify: false
        network_name: "prod-net"
        state: present
        network: "10.0.0.0/24"
        gateway: "10.0.0.1"
        network6: "2001:db8::/64"
        gateway6: "2001:db8::1"
        mac_prefix: "aa:00:00"

# Modify an existing network
- name: Update Ganeti network settings
    codefritzel.ganeti.gnt_network:
        rapi_address: "ganeti-cluster"
        rapi_port: 5080
        rapi_username: "admin"
        rapi_password: "secret"
        ssl_verify: false
        network_name: "prod-net"
        state: present
        gateway: "10.0.0.254"
        mac_prefix: "aa:11:22"
        job_poll: true
        poll_timeout: 120
        poll_interval: 2

# Remove a network
- name: Remove a Ganeti network
    codefritzel.ganeti.gnt_network:
        rapi_address: "ganeti-cluster"
        rapi_port: 5080
        rapi_username: "admin"
        rapi_password: "secret"
        ssl_verify: false
        network_name: "prod-net"
        state: absent

# Check mode - preview a network change
- name: Preview network changes
    codefritzel.ganeti.gnt_network:
        rapi_address: "ganeti-cluster"
        rapi_port: 5080
        rapi_username: "admin"
        rapi_password: "secret"
        ssl_verify: false
        network_name: "prod-net"
        state: present
        gateway: "10.0.0.254"
    check_mode: true

# Start a network change asynchronously
- name: Create a Ganeti network asynchronously
    codefritzel.ganeti.gnt_network:
        rapi_address: "ganeti-cluster"
        rapi_port: 5080
        rapi_username: "admin"
        rapi_password: "secret"
        ssl_verify: false
        network_name: "staging-net"
        state: present
        network: "10.20.0.0/24"
        gateway: "10.20.0.1"
        job_poll: false
    register: network_job

- name: Display background job ID
    ansible.builtin.debug:
        msg: "Network change started with job ID: {{ network_job.job_id }}"
"""

RETURN = r"""
---
changed:
    description: Whether any changes were made to the network.
    type: bool
    returned: always

msg:
    description: Human-readable message describing the action performed.
    type: str
    returned: always

job:
    description: Information about the executed Ganeti job.
    type: dict
    returned: when C(job_poll) is true and a job was created
    sample:
        id: 123
        status: success
        ops: ["network_add"]

job_id:
    description: ID of the background Ganeti job.
    type: int
    returned: when C(job_poll) is false
    sample: 123
"""


def ensure_present(module: AnsibleModule, client_wrapper: ClientWrapper):
    if client_wrapper.check_network_exists(module.params["network_name"]):
        network_name = module.params["network_name"]
        network = client_wrapper.rapi_client.network_service.get_network(network_name)
        network_dict = dataclass_to_dict(network)
        desired_params = {
            "network": module.params["network"],
            "gateway": module.params["gateway"],
            "network6": module.params["network6"],
            "gateway6": module.params["gateway6"],
            "mac_prefix": module.params["mac_prefix"],
        }
        diff_params = dict_diff(desired_params, network_dict)

        if diff_params != {}:
            if module.check_mode:
                module.exit_json(
                    changed=True,
                    msg=f"Network {network_name} would be modified.",
                )
            else:
                job_id = client_wrapper.rapi_client.network_service.modify_network(
                    network_name, **diff_params
                )
                job_dict = client_wrapper.return_job_or_wait_for_complete(job_id)
                module.exit_json(
                    changed=True,
                    msg=f"Network {network_name} modified. Job ID: {job_id}.",
                    job=job_dict,
                )
        else:
            module.exit_json(
                changed=False,
                msg=f"Network {network_name} already exists.",
            )
    else:
        if module.check_mode:
            module.exit_json(
                changed=True,
                msg=f"Network {module.params['network_name']} would be created.",
            )
        else:
            new_network = NewNetwork(
                network_name=module.params["network_name"],
                network=module.params["network"],
                gateway=module.params["gateway"],
                network6=module.params["network6"],
                gateway6=module.params["gateway6"],
                mac_prefix=module.params["mac_prefix"],
            )

            job_id = client_wrapper.rapi_client.network_service.create_network(
                new_network=new_network
            )

            job_dict = client_wrapper.return_job_or_wait_for_complete(job_id)
            module.exit_json(
                changed=True,
                msg=f"Network {module.params['network_name']} created.",
                job=job_dict,
            )


def ensure_absent(module: AnsibleModule, client_wrapper: ClientWrapper):
    if client_wrapper.check_network_exists(module.params["network_name"]):
        if module.check_mode:
            module.exit_json(
                changed=True,
                msg=f"Network {module.params['network_name']} would be removed.",
            )
        else:
            job_id = client_wrapper.rapi_client.network_service.delete_network(
                network_name=module.params["network_name"]
            )

            job_dict = client_wrapper.return_job_or_wait_for_complete(job_id)
            module.exit_json(
                changed=True,
                msg=f"Network {module.params['network_name']} removed.",
                job=job_dict,
            )
    else:
        module.exit_json(
            changed=False,
            msg=f"Network {module.params['network_name']} already removed.",
        )


def run_module():
    module_args = get_api_argument_spec()
    module_args.update(get_poll_argument_spec())
    module_args.update(
        state=dict(type="str", choices=["present", "absent"], default="present"),
        network_name=dict(type="str", required=True),
        network=dict(
            type="str", required=False, default=None
        ),  # IPv4 network address in CIDR notation, e.g. 10.0.0.0/24
        gateway=dict(type="str", required=False, default=None),
        network6=dict(
            type="str", required=False, default=None
        ),  # IPv6 network address in CIDR notation, e.g. 2001:db8::/64
        gateway6=dict(type="str", required=False, default=None),
        mac_prefix=dict(type="str", required=False, default=None),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    client_wrapper = ClientWrapper(module)

    state = module.params["state"]

    if state == "present":
        ensure_present(module, client_wrapper)
    elif state == "absent":
        ensure_absent(module, client_wrapper)
    else:
        module.fail_json(
            msg="Unknown state passed, please choose from [present, absent]!"
        )


def main():
    run_module()


if __name__ == "__main__":
    main()
