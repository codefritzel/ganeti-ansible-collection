class ModuleDocFragment:
    DOCUMENTATION = r"""
options:
    job_poll:
        description:
            - Whether to poll for job completion.
            - If false, the module returns immediately with the Ganeti job ID.
        type: bool
        default: true
        required: false
    poll_timeout:
        description:
            - Maximum time in seconds to wait for job completion.
            - Only used when C(job_poll) is true.
        type: int
        default: 1000
        required: false
    poll_interval:
        description:
            - Interval in seconds between job status polls.
            - Only used when C(job_poll) is true.
        type: int
        default: 2
        required: false
"""
