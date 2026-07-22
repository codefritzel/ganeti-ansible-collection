from ansible.module_utils.basic import AnsibleModule
from client.models.job import JOB_STATUS_SUCCESS

try:
    from client import GanetiRAPIClient as GntRapiClient, GanetiRAPIClient

    HAS_RAPI_CLIENT = True
except ImportError:
    HAS_RAPI_CLIENT = False
    GntRapiClient = None


class ClientWrapper:
    def __init__(self, module: AnsibleModule):
        if not HAS_RAPI_CLIENT:
            module.fail_json("Library GanetiRAPIClient not available.")

        self.module = module
        self._client = None
        self._initialize_client()

    def _initialize_client(self):
        try:
            self._client = GntRapiClient(
                rapi_address=f"{self.module.params['rapi_address']}:{self.module.params['rapi_port']}",
                username=self.module.params["rapi_username"],
                password=self.module.params["rapi_password"],
                ssl_verify=self.module.params["ssl_verify"],
            )

        except Exception as e:
            self.module.fail_json(
                msg="Failed to connect to GenetiRAPIClient, error: {}".format(e)
            )

    def return_job_or_wait_for_complete(self, job_id):
        if self.module.params["job_poll"]:
            job = self.rapi_client.job_service.wait_for_job(
                job_id,
                self.module.params["poll_timeout"],
                self.module.params["poll_interval"],
            )

            job_dict = job.__dict__
            if job.status != JOB_STATUS_SUCCESS:
                self.module.fail_json(
                    changed=False,
                    msg=f"Job {job_id} was not successful. Status: {job.status}",
                    job=job_dict,
                )

            return job_dict
        else:
            self.module.exit_json(
                changed=True, msg=f"Job {job_id} started.", job_id=job_id
            )

    def get_job_info(self, job_id: int) -> dict:
        return self._client.job_service.get_job_info(job_id)

    def check_instance_exists(self, instance_name: str) -> bool:
        return instance_name in self._client.instance_service.get_instance_names()

    @property
    def rapi_client(self) -> GanetiRAPIClient:
        return self._client


def get_poll_argument_spec():
    return dict(
        job_poll=dict(type="bool", default=True),
        poll_timeout=dict(type="int", default=1000),
        poll_interval=dict(type="int", default=2),
    )


def get_api_argument_spec():
    return dict(
        rapi_address=dict(type="str", required=True),
        rapi_port=dict(type="int", required=True),
        rapi_username=dict(type="str", required=True),
        rapi_password=dict(type="str", required=True, no_log=True),
        ssl_verify=dict(type="bool", default=True),
        timeout=dict(type="int", default=5),
    )
