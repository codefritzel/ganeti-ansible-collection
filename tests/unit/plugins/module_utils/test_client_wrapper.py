from ansible.module_utils.basic import AnsibleModule
from client import GanetiRAPIClient
from client.models.job import Job, JOB_STATUS_SUCCESS, JOB_STATUS_ERROR

import pytest

from plugins.module_utils.client_wrapper import ClientWrapper
from unit.ansible_exception import AnsibleFailJson, AnsibleExitJson


class TestReturnJobOrWaitForComplete:
    def test_waits_and_returns_job_dict(
        self,
        module: AnsibleModule,
        client_wrapper: ClientWrapper,
        rapi_client: GanetiRAPIClient,
    ):
        module.params = {"job_poll": True, "poll_timeout": 60, "poll_interval": 5}

        job_id = 123
        job = Job(
            status=JOB_STATUS_SUCCESS,
            id=job_id,
            opresult=["ok"],
            ops=[],
            summary=[],
            opstatus=[],
        )
        rapi_client.job_service.wait_for_job.return_value = job

        result = client_wrapper.return_job_or_wait_for_complete(job_id)

        rapi_client.job_service.wait_for_job.assert_called_once_with(
            job_id, module.params["poll_timeout"], module.params["poll_interval"]
        )
        assert result == job.__dict__

    def test_fails_when_job_not_successful(
        self,
        module: AnsibleModule,
        client_wrapper: ClientWrapper,
        rapi_client: GanetiRAPIClient,
    ):
        module.params = {"job_poll": True, "poll_timeout": 60, "poll_interval": 5}

        job_id = 123
        job = Job(
            status=JOB_STATUS_ERROR,
            id=job_id,
            opresult=["ok"],
            ops=[],
            summary=[],
            opstatus=[],
        )
        rapi_client.job_service.wait_for_job.return_value = job

        with pytest.raises(AnsibleFailJson) as exc_info:
            client_wrapper.return_job_or_wait_for_complete(job_id)

        result = exc_info.value.kwargs
        assert result["failed"] is True
        assert result["changed"] is False
        assert result["msg"] == "Job 123 was not successful. Status: error"

    def test_exits_when_job_poll_false(
        self,
        module: AnsibleModule,
        client_wrapper: ClientWrapper,
        rapi_client: GanetiRAPIClient,
    ):
        module.params = {
            "job_poll": False,
        }

        job_id = 123

        with pytest.raises(AnsibleExitJson) as exc_info:
            client_wrapper.return_job_or_wait_for_complete(job_id)

        rapi_client.job_service.wait_for_job.assert_not_called()

        result = exc_info.value.kwargs
        assert result["changed"] is True
        assert result["msg"] == "Job 123 started."
        assert result["job_id"] == job_id
