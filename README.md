# Ganeti Ansible Collection

Ansible collection for managing [Ganeti](https://www.ganeti.org/) instances through the Ganeti Remote API (RAPI).

## Requirements

* Ansible Core with collection support
* A reachable Ganeti cluster with RAPI enabled
* The `GanetiRAPIClient` Python library installed on the managed node
* Network connectivity from the managed node to the Ganeti RAPI endpoint
* A Ganeti user with sufficient permissions for the requested operations

The Python dependency is listed in [requirements.txt](requirements.txt):

```bash
pip install -r requirements.txt
```

## Installation

### From a built collection archive

```bash
ansible-galaxy collection install codefritzel-ganeti-0.0.1.tar.gz
```

### Build from source

Run the following commands from the collection root:

```bash
ansible-galaxy collection build
ansible-galaxy collection install codefritzel-ganeti-0.0.1.tar.gz
```

## RAPI connection parameters

Both modules accept the following connection parameters:

| Parameter | Required | Default | Description |
| --- | --- | --- | --- |
| `rapi_address` | Yes | — | Hostname or IP address of the RAPI server |
| `rapi_port` | Yes | — | RAPI port, commonly `5080` |
| `rapi_username` | Yes | — | RAPI username |
| `rapi_password` | Yes | — | RAPI password; not logged by Ansible |
| `ssl_verify` | No | `true` | Verify the RAPI server TLS certificate |
| `timeout` | No | `5` | Connection timeout in seconds |


## Asynchronous jobs

Set `job_poll: false` to start an operation without waiting for completion:

```yaml
- name: Start instance creation without waiting
  codefritzel.ganeti.gnt_instance:
    api_address: "{{ ganeti_rapi_address }}"
    rapi_port: 5080
    rapi_username: "{{ ganeti_rapi_username }}"
    rapi_password: "{{ ganeti_rapi_password }}"
    instance_name: batch-01.example.org
    state: present
    disk_template: plain
    os: instance-guestfish+ubuntu-noble
    beparams:
      vcpus: 4
      memory: 4096
    pnode: node1.example.org
    job_poll: false
    register: instance_job

- name: Retrieve the job status
  codefritzel.ganeti.gnt_job_info:
    rapi_address: "{{ ganeti_rapi_address }}"
    rapi_port: 5080
    rapi_username: "{{ ganeti_rapi_username }}"
    rapi_password: "{{ ganeti_rapi_password }}"
    job_id: "{{ instance_job.job_id }}"
  register: job_result

- name: Display the job status
  ansible.builtin.debug:
    msg: "Job {{ job_result.job_info.id }}: {{ job_result.job_info.status }}"
```

When polling is enabled, `poll_timeout` and `poll_interval` control how long and how often the module waits for the job. The current defaults are `1000` seconds for `poll_timeout` and `2` seconds for `poll_interval`.

## Check mode

All modules support Ansible check mode. For example:

```yaml
- name: Preview an instance modification
  codefritzel.ganeti.gnt_instance:
    rapi_address: "{{ ganeti_rapi_address }}"
    rapi_port: 5080
    rapi_username: "{{ ganeti_rapi_username }}"
    rapi_password: "{{ ganeti_rapi_password }}"
    instance_name: web-01.example.org
    state: present
    beparams:
      memory: 4096
  check_mode: true
```

## Development and testing

Development dependencies are listed in [requirements-dev.txt](requirements-dev.txt):

```bash
pip install -r requirements-dev.txt
pytest
```

Unit tests are located under [tests/unit](tests/unit). Integration tests are located under [tests/integration](tests/integration) and require a configured environment (Docker). Collection sanity checks can be run with `ansible-test`.

## Known limitations

* The RAPI client library must be available on the managed node.
* The collection is currently in early development; validate permissions, TLS settings, instance policies, and OS providers before using it in production.
