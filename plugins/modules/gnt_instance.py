from ansible.module_utils.basic import AnsibleModule
from client.models.instance import NewInstance, BackendParams
from client.utils import dataclass_to_dict

try:
    from ansible_collections.codefritzel.ganeti.plugins.module_utils.client_wrapper import (
        get_api_argument_spec,
        get_poll_argument_spec,
        ClientWrapper,
    )
    from ansible_collections.codefritzel.ganeti.plugins.module_utils.utils import (
        dict_diff,
    )
except ImportError:
    # only for tests
    from plugins.module_utils.utils import dict_diff
    from plugins.module_utils.client_wrapper import (
        get_api_argument_spec,
        ClientWrapper,
        get_poll_argument_spec,
    )


DOCUMENTATION = r"""
---
module: gnt_instance
short_description: Manage Ganeti instances
description:
  - Manage Ganeti instances on a Ganeti cluster via RAPI.
  - Supports creating, deleting, starting, stopping, and migrating instances.
  - Can modify instance parameters for existing instances.
version_added: "0.0.1"
extends_documentation_fragment:
  - codefritzel.ganeti.ganeti_rapi

options:
  instance_name:
    description:
      - Name of the Ganeti instance to manage.
      - Must be a valid hostname.
    type: str
    required: true

  state:
    description:
      - Desired state of the instance.
      - C(present) - Ensure the instance exists and is configured.
      - C(absent) - Remove the instance.
      - C(started) - Ensure the instance is running.
      - C(stopped) - Ensure the instance is stopped.
      - C(migrated) - Migrate the instance to another node.
      - C(failover) - Perform a failover of the instance.
    type: str
    choices: ['present', 'absent', 'started', 'stopped', 'migrated', 'failover']
    default: present

  disk_template:
    description:
      - Disk template for the instance.
      - Required when creating a new instance.
      - Examples are 'plain', 'drbd', 'diskless'.
    type: str
    required: false

  beparams:
    description:
      - Backend parameters for the instance.
      - Only used when creating or modifying instances.
    type: dict
    required: false
    suboptions:
      vcpus:
        description: Number of virtual CPUs.
        type: int
      memory:
        description: Amount of RAM in MB.
        type: int
      minmem:
        description: Minimum memory in MB.
        type: int
      maxmem:
        description: Maximum memory in MB.
        type: int

  hvparams:
    description:
      - Hypervisor parameters for the instance.
      - Key-value pairs specific to the hypervisor type.
    type: dict
    required: false

  os:
    description:
      - Operating system for the instance.
      - Required when creating a new instance.
      - Example is 'instance-guestfish+ubuntu-noble'.
    type: str
    required: false

  osparams:
    description:
      - Operating system parameters.
      - Key-value pairs specific to the OS interface.
    type: dict
    required: false

  disks:
    description:
      - List of disk configurations.
      - Used when creating instances.
      - Note that disks cannot be modified after creation.
    type: list
    required: false

  nics:
    description:
      - List of network interface configurations.
      - Used when creating instances.
      - Note that NICs are excluded from modification operations.
    type: list
    required: false

  pnode:
    description:
      - Primary node for the instance.
      - Required for DRBD disk templates.
    type: str
    required: false

  snode:
    description:
      - Secondary node for the instance.
      - Only used with DRBD disk template.
    type: str
    required: false

  start:
    description:
      - Whether to start the instance after creation.
    type: bool
    default: true
    required: false

  ip_check:
    description:
      - Whether to check if the instance IP is already in use.
    type: bool
    default: false
    required: false

  name_check:
    description:
      - Whether to check if the instance name is valid.
    type: bool
    default: false
    required: false

  ignore_ipolicy:
    description:
      - Whether to ignore the cluster's instance policy.
    type: bool
    default: false
    required: false

  job_poll:
    description:
      - Whether to poll for job completion.
      - If false, returns immediately with job ID.
    type: bool
    default: true
    required: false

  poll_timeout:
    description:
      - Maximum time in seconds to wait for job completion.
      - Only used when job_poll is true.
    type: int
    default: 30
    required: false

  poll_interval:
    description:
      - Interval in seconds between job status polls.
      - Only used when job_poll is true.
    type: int
    default: 1
    required: false
"""

EXAMPLES = r"""
---
# Create a new instance
- name: Create a new Ganeti instance
  codefritzel.ganeti.gnt_instance:
    rapi_address: "ganeti-cluster:5080"
    rapi_username: "admin"
    rapi_password: "secret"
    rapi_ssl_verify: false
    instance_name: "web-server-01"
    state: present
    disk_template: "drbd"
    beparams:
      vcpus: 4
      memory: 2048
      minmem: 512
      maxmem: 4096
    hvparams:
      kernel_path: "/boot/vmlinuz"
    os: "instance-guestfish+ubuntu-noble"
    osparams:
      install_size: "50G"
    pnode: "node1"
    snode: "node2"
    start: true
    ip_check: true
    name_check: true

# Create instance without starting it
- name: Create instance in stopped state
  codefritzel.ganeti.gnt_instance:
    rapi_address: "ganeti-cluster:5080"
    rapi_username: "admin"
    rapi_password: "secret"
    instance_name: "db-server-01"
    state: present
    disk_template: "plain"
    beparams:
      vcpus: 8
      memory: 8192
    os: "instance-guestfish+ubuntu-noble"
    pnode: "node1"
    start: false

# Modify an existing instance
- name: Increase memory of an instance
  codefritzel.ganeti.gnt_instance:
    rapi_address: "ganeti-cluster:5080"
    rapi_username: "admin"
    rapi_password: "secret"
    instance_name: "web-server-01"
    state: present
    beparams:
      memory: 4096
      maxmem: 8192
    job_poll: true
    poll_timeout: 60

# Start an instance
- name: Start instance
  codefritzel.ganeti.gnt_instance:
    rapi_address: "ganeti-cluster:5080"
    rapi_username: "admin"
    rapi_password: "secret"
    instance_name: "web-server-01"
    state: started

# Stop an instance
- name: Stop instance
  codefritzel.ganeti.gnt_instance:
    rapi_address: "ganeti-cluster:5080"
    rapi_username: "admin"
    rapi_password: "secret"
    instance_name: "web-server-01"
    state: stopped

# Migrate instance to another node
- name: Migrate instance
  codefritzel.ganeti.gnt_instance:
    rapi_address: "ganeti-cluster:5080"
    rapi_username: "admin"
    rapi_password: "secret"
    instance_name: "web-server-01"
    state: migrated
    job_poll: true
    poll_timeout: 120

# Perform instance failover
- name: Failover instance
  codefritzel.ganeti.gnt_instance:
    rapi_address: "ganeti-cluster:5080"
    rapi_username: "admin"
    rapi_password: "secret"
    instance_name: "critical-db"
    state: failover

# Delete an instance
- name: Remove instance
  codefritzel.ganeti.gnt_instance:
    rapi_address: "ganeti-cluster:5080"
    rapi_username: "admin"
    rapi_password: "secret"
    instance_name: "web-server-01"
    state: absent

# Check mode - plan changes without executing
- name: Check what would be changed
  codefritzel.ganeti.gnt_instance:
    rapi_address: "ganeti-cluster:5080"
    rapi_username: "admin"
    rapi_password: "secret"
    instance_name: "web-server-01"
    state: present
    beparams:
      memory: 8192
  check_mode: true

# Create instance without waiting for job completion
- name: Create instance asynchronously
  codefritzel.ganeti.gnt_instance:
    rapi_address: "ganeti-cluster:5080"
    rapi_username: "admin"
    rapi_password: "secret"
    instance_name: "web-server-02"
    state: present
    disk_template: "drbd"
    beparams:
      vcpus: 2
      memory: 1024
    os: "instance-guestfish+ubuntu-noble"
    pnode: "node1"
    snode: "node2"
    job_poll: false
  register: instance_job

- name: Display job ID
  debug:
    msg: "Instance creation started with job ID: {{ instance_job.job_id }}"

# Modify instance in check mode
- name: Plan instance modification
  codefritzel.ganeti.gnt_instance:
    rapi_address: "ganeti-cluster:5080"
    rapi_username: "admin"
    rapi_password: "secret"
    instance_name: "web-server-01"
    state: present
    beparams:
      vcpus: 6
      memory: 6144
  check_mode: true
  register: modification_plan

- name: Show planned changes
  debug:
    msg: "{{ modification_plan }}"
"""

RETURN = r"""
---
changed:
  description: Whether any changes were made to the instance.
  type: bool
  returned: always

msg:
  description: Human-readable message describing the action performed.
  type: str
  returned: always

job:
  description: Information about the executed job (if applicable).
  type: dict
  returned: when job_poll is true or job was created
  sample:
    id: 123
    status: success
    ops: ["instance_create"]

job_id:
  description: ID of the background job (only when job_poll is false).
  type: int
  returned: when job_poll is false
  sample: 123
"""

MODULE_STATES = ["present", "absent", "started", "stopped", "migrated"]

DISK_TEMPLATES = [
    "sharedfile",
    "diskless",
    "plain",
    "gluster",
    "blockdev",
    "drbd",
    "ext",
    "file",
    "rbd",
]


def ensure_present(module: AnsibleModule, client: ClientWrapper):
    if client.check_instance_exists(module.params["instance_name"]):
        # modify existing instance if parameters differ, otherwise do nothing
        instance_name = module.params["instance_name"]
        instance = client.rapi_client.instance_service.get_instance(instance_name)
        instance_dict = dataclass_to_dict(instance)
        del module.params["instance_name"]

        diff_params = dict_diff(module.params, instance_dict, ["disks", "nics"])

        if diff_params != {}:
            if module.check_mode:
                module.exit_json(
                    changed=True,
                    msg=f"Instance {instance_name} would be modified.",
                )
            else:
                job_id = client.rapi_client.instance_service.modify_instance(
                    instance_name, **diff_params
                )
                job_dict = client.return_job_or_wait_for_complete(job_id)
                module.exit_json(
                    changed=True,
                    msg=f"Instance {instance_name} modified. Job ID: {job_id}.",
                    job=job_dict,
                )
        else:
            module.exit_json(
                changed=False,
                msg=f"Instance {instance_name} already exists.",
            )
    else:
        # create new instance
        if module.check_mode:
            module.exit_json(
                changed=True,
                msg=f"Instance {module.params['instance_name']} would be created.",
            )
        else:
            new_instance = NewInstance(
                instance_name=module.params["instance_name"],
                disk_template=module.params["disk_template"],
                beparams=BackendParams(**module.params["beparams"]),
                hvparams=module.params.get("hvparams", None),
                os=module.params["os"],
                osparams=module.params.get("osparams", None),
                disks=module.params.get("disks", []),
                nics=module.params.get("nics", []),
                pnode=module.params.get("pnode", None),
                snode=module.params.get("snode", None),
            )

            job_id = client.rapi_client.instance_service.create_instance(
                new_instance=new_instance,
                start=bool(module.params.get("start", True)),
                ip_check=bool(module.params.get("ip_check", False)),
                name_check=bool(module.params.get("name_check", False)),
                ignore_ipolicy=bool(module.params.get("ignore_ipolicy", False)),
            )
            job_dict = client.return_job_or_wait_for_complete(job_id)
            module.exit_json(
                changed=True,
                msg=f"Instance {module.params['instance_name']} created. Job ID: {job_id}.",
                job=job_dict,
            )


def ensure_absent(module: AnsibleModule, client: ClientWrapper):
    if client.check_instance_exists(module.params["instance_name"]):
        if not module.check_mode:
            job_id = client.rapi_client.instance_service.delete_instance(
                instance_name=module.params["instance_name"]
            )

            job_dict = client.return_job_or_wait_for_complete(job_id)
            module.exit_json(
                changed=True,
                msg=f"Instance {module.params['instance_name']} removed. Job ID: {job_id}",
                job=job_dict,
            )
        else:
            module.exit_json(
                changed=True,
                msg=f"Instance {module.params['instance_name']} would be removed.",
            )
    else:
        module.exit_json(
            changed=False,
            msg=f"Instance {module.params['instance_name']} is already removed.",
        )


def ensure_started(module: AnsibleModule, client: ClientWrapper):
    if client.check_instance_exists(module.params["instance_name"]):
        instance = client.rapi_client.instance_service.get_instance(
            instance_name=module.params["instance_name"]
        )
        if not instance.is_running():
            if not module.check_mode:
                job_id = client.rapi_client.instance_service.start_instance(
                    instance_name=module.params["instance_name"]
                )

                job_dict = client.return_job_or_wait_for_complete(job_id)
                module.exit_json(
                    changed=True,
                    msg=f"Instance {module.params['instance_name']} started. Job ID: {job_id}",
                    job=job_dict,
                )
            else:
                module.exit_json(
                    changed=True,
                    msg=f"Instance {module.params['instance_name']} would be started.",
                )
        else:
            module.exit_json(
                changed=True,
                msg=f"Instance {module.params['instance_name']} is already started.",
            )
    else:
        module.fail_json(
            changed=False,
            msg=f"Instance {module.params['instance_name']} does not exists.",
        )


def ensure_stopped(module: AnsibleModule, client: ClientWrapper):
    if client.check_instance_exists(module.params["instance_name"]):
        instance = client.rapi_client.instance_service.get_instance(
            instance_name=module.params["instance_name"]
        )
        if instance.is_stopped():  # check instance is stopped
            if not module.check_mode:
                job_id = client.rapi_client.instance_service.stop_instance(
                    instance_name=module.params["instance_name"]
                )

                job_dict = client.return_job_or_wait_for_complete(job_id)
                module.exit_json(
                    changed=True,
                    msg=f"Instance {module.params['instance_name']} started. Job ID: {job_id}",
                    job=job_dict,
                )
            else:
                module.exit_json(
                    changed=True,
                    msg=f"Instance {module.params['instance_name']} would be stopped.",
                )
        else:
            module.exit_json(
                changed=True,
                msg=f"Instance {module.params['instance_name']} is already stopped.",
            )
    else:
        module.fail_json(
            changed=False,
            msg=f"Instance {module.params['instance_name']} does not exists.",
        )


def ensure_migrated(module: AnsibleModule, client: ClientWrapper):
    if client.check_instance_exists(module.params["instance_name"]):
        instance = client.rapi_client.instance_service.get_instance(
            instance_name=module.params["instance_name"]
        )
        if instance.is_running():
            if not module.check_mode:
                job_id = client.rapi_client.instance_service.migrate_instance(
                    instance_name=module.params["instance_name"]
                )

                job_dict = client.return_job_or_wait_for_complete(job_id)
                module.exit_json(
                    changed=True,
                    msg=f"Instance {module.params['instance_name']} migrated. Job ID: {job_id}",
                    job=job_dict,
                )
            else:
                module.exit_json(
                    changed=True,
                    msg=f"Instance {module.params['instance_name']} would be migrated.",
                )
        else:
            module.fail_json(
                changed=False,
                msg=f"Instance {module.params['instance_name']} must be running in order to be migrated.",
            )
    else:
        module.fail_json(
            changed=False,
            msg=f"Instance {module.params['instance_name']} does not exists.",
        )


def ensure_failover(module: AnsibleModule, client: ClientWrapper):
    if client.check_instance_exists(module.params["instance_name"]):
        instance = client.rapi_client.instance_service.get_instance(
            instance_name=module.params["instance_name"]
        )
        if instance.is_running():  # check instance is running
            if not module.check_mode:
                job_id = client.rapi_client.instance_service.migrate_instance(
                    instance_name=module.params["instance_name"]
                )

                job_dict = client.return_job_or_wait_for_complete(job_id)
                module.exit_json(
                    changed=True,
                    msg=f"Instance {module.params['instance_name']} failover. Job ID: {job_id}",
                    job=job_dict,
                )
            else:
                module.exit_json(
                    changed=True,
                    msg=f"Instance {module.params['instance_name']} would be failover.",
                )
        else:
            module.fail_json(
                changed=False,
                msg=f"Instance {module.params['instance_name']} must be stopped in order to be failover.",
            )
    else:
        module.fail_json(
            changed=False,
            msg=f"Instance {module.params['instance_name']} does not exists.",
        )


def run_module():
    module_args = get_api_argument_spec()
    module_args.update(get_poll_argument_spec())
    module_args.update(
        state=dict(type="str", choices=MODULE_STATES, default="present"),
        instance_name=dict(type="str", required=True),
        ip_check=dict(type="bool", required=False),
        name_check=dict(type="bool", required=False),
        start=dict(type="bool", required=False),
        ignore_ipolicy=dict(type="bool", required=False),
        disk_template=dict(type="str", choices=DISK_TEMPLATES, required=False),
        os=dict(type="str", required=False),
        osparams=dict(type="dict", required=False),
        disks=dict(type="list", required=False),
        nics=dict(type="list", required=False),
        pnode=dict(type="str", required=False),
        snode=dict(type="str", required=False),
        hvparams=dict(type="dict", required=False),
        beparams=dict(
            type="dict",
            required=False,
            options=dict(
                vcpus=dict(type="int", required=False),
                memory=dict(type="int", required=False),
                minmem=dict(type="int", required=False),
                maxmem=dict(type="int", required=False),
            ),
        ),
    )

    module: AnsibleModule = AnsibleModule(
        argument_spec=module_args, supports_check_mode=True
    )
    client_wrapper = ClientWrapper(module)

    state = module.params["state"]

    if state == "present":
        ensure_present(module, client_wrapper)
    elif state == "absent":
        ensure_absent(module, client_wrapper)
    elif state == "started":
        ensure_started(module, client_wrapper)
    elif state == "stopped":
        ensure_stopped(module, client_wrapper)
    elif state == "migrated":
        ensure_migrated(module, client_wrapper)
    elif state == "failover":
        ensure_failover(module, client_wrapper)
    else:
        module.fail_json(
            msg=f"Unknown state passed, please choose from {MODULE_STATES}!"
        )


def main():
    run_module()


if __name__ == "__main__":
    main()
