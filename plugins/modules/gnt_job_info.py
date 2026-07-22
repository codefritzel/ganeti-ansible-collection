#!/usr/bin/python
# -*- coding: utf-8 -*-


from ansible.module_utils.basic import AnsibleModule

try:
    from ansible_collections.codefritzel.ganeti.plugins.module_utils.client_wrapper import (
        get_api_argument_spec,
        ClientWrapper,
    )
except ImportError:
    from plugins.module_utils.client_wrapper import (
        get_api_argument_spec,
        ClientWrapper,
    )  # only for tests


DOCUMENTATION = r"""
---
module: gnt_job_info
short_description: Retrieve information about a Ganeti job
version_added: "1.0.0"
description:
    - This module retrieves detailed information about a specific Ganeti job.
    - It queries the Ganeti RAPI (Remote API) to get the status and details of a job by its ID.
    - Useful for monitoring and tracking the execution status of Ganeti operations.
author:
    - codefritzel
options:
    job_id:
        description:
            - The unique identifier of the Ganeti job to retrieve information about.
        type: int
        required: true
extends_documentation_fragment:
    - codefritzel.ganeti.ganeti_rapi
"""

EXAMPLES = r"""
- name: Get job info and register the result
  codefritzel.ganeti.gnt_job_info:
    rapi_address: "ganeti.example.com"
    rapi_port: 5080
    rapi_username: "admin"
    rapi_password: "secret"
    job_id: 12345
  register: job_result

- name: Display job status
  ansible.builtin.debug:
    msg: "Job {{ job_result.job_info.id }} status: {{ job_result.job_info.status }}"

- name: Wait until job is completed
  codefritzel.ganeti.gnt_job_info:
    rapi_address: "{{ ganeti_cluster }}"
    rapi_port: 5080
    rapi_username: "{{ ganeti_user }}"
    rapi_password: "{{ ganeti_password }}"
    ssl_verify: false
    job_id: "{{ previous_operation.job_id }}"
  register: job_status
  until: job_status.job_info.status in ['success', 'error', 'canceled']
  retries: 30
  delay: 10
"""

RETURN = r"""
job_info:
    description: Detailed information about the Ganeti job
    returned: always
    type: dict
    sample: {
        "id": 12345,
        "status": "success",
        "ops": [
            {
                "OP_ID": "OP_INSTANCE_CREATE",
                "instance_name": "instance01.example.com",
                "status": "success"
            }
        ],
        "opresult": [
            "instance01.example.com"
        ],
        "opstatus": [
            "success"
        ],
        "summary": [
            "INSTANCE_CREATE(instance01.example.com)"
        ]
    }
changed:
    description: Whether any changes were made (always false for info modules)
    returned: always
    type: bool
    sample: false
"""


def run_module():
    module_args = get_api_argument_spec()
    module_args.update(
        job_id=dict(type="int", required=True),
    )

    module: AnsibleModule = AnsibleModule(
        argument_spec=module_args, supports_check_mode=True
    )

    client_wrapper = ClientWrapper(module)
    job_info = client_wrapper.get_job_info(job_id=module.params["job_id"])
    module.exit_json(changed=False, job_info=job_info.__dict__)


def main():
    run_module()


if __name__ == "__main__":
    main()
