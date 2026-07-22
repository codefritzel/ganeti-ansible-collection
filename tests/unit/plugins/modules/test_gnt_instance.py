from unittest.mock import MagicMock

import pytest
from ansible.module_utils.basic import AnsibleModule
from client.models.job import Job, JOB_STATUS_SUCCESS, JOB_STATUS_ERROR

from plugins.module_utils.client_wrapper import ClientWrapper
from plugins.modules import gnt_instance
from unit.ansible_exception import AnsibleExitJson, AnsibleFailJson


class TestEnsurePresentFunction:
    def test_ensure_present_instance_exists(
        self,
        module: AnsibleModule,
        client_wrapper: ClientWrapper,
        rapi_client,
        monkeypatch,
    ):
        module.params = {
            "rapi_address": "mycluster:409",
            "rapi_username": "asdd",
            "rapi_ssl_verify": False,
            "rapi_password": "sdf",
            "instance_name": "myinstance",
        }
        module.check_mode = True

        rapi_client.instance_service.get_instance_names.return_value = ["myinstance"]
        rapi_client.instance_service.create_instance.return_value = None
        monkeypatch.setattr(gnt_instance, "dict_diff", lambda *args, **kwargs: {})

        with pytest.raises(AnsibleExitJson) as exc:
            gnt_instance.ensure_present(module, client_wrapper)

        result = exc.value.kwargs
        rapi_client.instance_service.create_instance.assert_not_called()
        assert result["changed"] is False
        assert result["msg"] == "Instance myinstance already exists."

    def test_ensure_present_instance_not_exists_check_mode(
        self, module: AnsibleModule, client_wrapper: ClientWrapper, rapi_client
    ):
        module.params = {
            "rapi_address": "mycluster:409",
            "rapi_username": "asdd",
            "rapi_ssl_verify": False,
            "rapi_password": "sdf",
            "instance_name": "myinstance",
        }
        module.check_mode = True

        rapi_client.instance_service.get_instance_names.return_value = []
        rapi_client.instance_service.create_instance.return_value = None

        with pytest.raises(AnsibleExitJson) as exc:
            gnt_instance.ensure_present(module, client_wrapper)

        result = exc.value.kwargs
        rapi_client.instance_service.create_instance.assert_not_called()
        assert result["changed"] is True
        assert result["msg"] == "Instance myinstance would be created."

    def test_ensure_present_instance_not_exists_pull_job_successful(
        self, module: AnsibleModule, client_wrapper: ClientWrapper, rapi_client
    ):
        module.params = {
            "rapi_address": "mycluster:409",
            "rapi_username": "asdd",
            "rapi_ssl_verify": False,
            "rapi_password": "sdf",
            "instance_name": "myinstance",
            "disk_template": "drbd",
            "beparams": {"vcpus": 1, "memory": 1024},
            "hvparams": {},
            "os": "instance-guestfish+ubuntu-noble",
            "osparams": {},
            "disks": [],
            "nics": [],
            "pnode": None,
            "snode": None,
            "start": True,
            "ip_check": False,
            "name_check": False,
            "ignore_ipolicy": False,
            "job_poll": True,
            "poll_timeout": 30,
            "poll_interval": 1,
        }

        rapi_client.instance_service.get_instance_names.return_value = []
        rapi_client.instance_service.create_instance.return_value = 123
        rapi_client.job_service.wait_for_job.return_value = Job(
            id=123,
            status=JOB_STATUS_SUCCESS,
            ops=[],
            summary=[],
            opstatus=[],
            opresult=[],
        )

        with pytest.raises(AnsibleExitJson) as exc:
            gnt_instance.ensure_present(module, client_wrapper)

        rapi_client.instance_service.create_instance.assert_called_once()
        result = exc.value.kwargs

        assert result["changed"] is True
        assert result["msg"] == "Instance myinstance created. Job ID: 123."

    def test_ensure_present_instance_not_exists_pull_job_error(
        self, module: AnsibleModule, client_wrapper: ClientWrapper, rapi_client
    ):
        module.params = {
            "rapi_address": "mycluster:409",
            "rapi_username": "asdd",
            "rapi_ssl_verify": False,
            "rapi_password": "sdf",
            "instance_name": "myinstance",
            "disk_template": "drbd",
            "beparams": {"vcpus": 1, "memory": 1024},
            "hvparams": {},
            "os": "instance-guestfish+ubuntu-noble",
            "osparams": {},
            "disks": [],
            "nics": [],
            "pnode": None,
            "snode": None,
            "start": True,
            "ip_check": False,
            "name_check": False,
            "ignore_ipolicy": False,
            "job_poll": True,
            "poll_timeout": 30,
            "poll_interval": 1,
        }

        rapi_client.instance_service.get_instance_names.return_value = []
        rapi_client.instance_service.create_instance.return_value = 123
        rapi_client.job_service.wait_for_job.return_value = Job(
            id=123,
            status=JOB_STATUS_ERROR,
            ops=[],
            summary=[],
            opstatus=[],
            opresult=[],
        )

        with pytest.raises(AnsibleFailJson) as exc:
            gnt_instance.ensure_present(module, client_wrapper)

        rapi_client.instance_service.create_instance.assert_called_once()
        result = exc.value.kwargs

        assert result["changed"] is False
        assert result["msg"] == "Job 123 was not successful. Status: error"

    def test_ensure_present_instance_not_exists_without_job_poll(
        self, module: AnsibleModule, client_wrapper: ClientWrapper, rapi_client
    ):
        module.params = {
            "rapi_address": "mycluster:409",
            "rapi_username": "asdd",
            "rapi_ssl_verify": False,
            "rapi_password": "sdf",
            "instance_name": "myinstance",
            "disk_template": "drbd",
            "beparams": {"vcpus": 1, "memory": 1024},
            "hvparams": {},
            "os": "instance-guestfish+ubuntu-noble",
            "osparams": {},
            "disks": [],
            "nics": [],
            "pnode": None,
            "snode": None,
            "start": True,
            "ip_check": False,
            "name_check": False,
            "ignore_ipolicy": False,
            "job_poll": False,
        }

        rapi_client.instance_service.get_instance_names.return_value = []
        rapi_client.instance_service.create_instance.return_value = 123

        with pytest.raises(AnsibleExitJson) as exc:
            gnt_instance.ensure_present(module, client_wrapper)

        rapi_client.instance_service.create_instance.assert_called_once()
        rapi_client.job_service.wait_for_job.assert_not_called()

        result = exc.value.kwargs
        assert result["changed"]
        assert result["msg"] == "Job 123 started."
        assert result["job_id"] == 123

    def test_ensure_present_instance_exists_with_diff_check_mode(
        self,
        module: AnsibleModule,
        client_wrapper: ClientWrapper,
        rapi_client,
        monkeypatch,
    ):
        module.params = {
            "rapi_address": "mycluster:409",
            "rapi_username": "asdd",
            "rapi_ssl_verify": False,
            "rapi_password": "sdf",
            "instance_name": "myinstance",
            "beparams": {"vcpus": 2, "memory": 2048},
            "hvparams": {},
        }
        module.check_mode = True

        # Mock instance with ohther values
        mock_instance = MagicMock()
        mock_instance.beparams = {"vcpus": 1, "memory": 1024}

        rapi_client.instance_service.get_instance_names.return_value = ["myinstance"]
        rapi_client.instance_service.get_instance.return_value = mock_instance

        with pytest.raises(AnsibleExitJson) as exc:
            gnt_instance.ensure_present(module, client_wrapper)

        result = exc.value.kwargs
        rapi_client.instance_service.modify_instance.assert_not_called()
        assert result["changed"] is True
        assert result["msg"] == "Instance myinstance would be modified."

    def test_ensure_present_instance_exists_with_diff_successful_modification(
        self,
        module: AnsibleModule,
        client_wrapper: ClientWrapper,
        rapi_client,
        monkeypatch,
    ):
        module.params = {
            "rapi_address": "mycluster:409",
            "rapi_username": "asdd",
            "rapi_ssl_verify": False,
            "rapi_password": "sdf",
            "instance_name": "myinstance",
            "beparams": {"vcpus": 2, "memory": 2048},
            "hvparams": {},
            "job_poll": True,
            "poll_timeout": 30,
            "poll_interval": 1,
        }
        module.check_mode = False

        mock_instance = MagicMock()
        mock_instance.beparams = {"vcpus": 1, "memory": 1024}

        rapi_client.instance_service.get_instance_names.return_value = ["myinstance"]
        rapi_client.instance_service.get_instance.return_value = mock_instance
        rapi_client.instance_service.modify_instance.return_value = 456
        rapi_client.job_service.wait_for_job.return_value = Job(
            id=456,
            status=JOB_STATUS_SUCCESS,
            ops=[],
            summary=[],
            opstatus=[],
            opresult=[],
        )

        with pytest.raises(AnsibleExitJson) as exc:
            gnt_instance.ensure_present(module, client_wrapper)

        result = exc.value.kwargs
        rapi_client.instance_service.modify_instance.assert_called_once()
        assert result["changed"] is True
        assert result["msg"] == "Instance myinstance modified. Job ID: 456."
        assert "job" in result

    def test_ensure_present_instance_exists_without_diff(
        self,
        module: AnsibleModule,
        client_wrapper: ClientWrapper,
        rapi_client,
        monkeypatch,
    ):
        module.params = {
            "rapi_address": "mycluster:409",
            "rapi_username": "asdd",
            "rapi_ssl_verify": False,
            "rapi_password": "sdf",
            "instance_name": "myinstance",
            "beparams": {"vcpus": 1, "memory": 1024},
            "hvparams": {},
            "job_poll": True,
            "poll_timeout": 30,
            "poll_interval": 1,
        }
        module.check_mode = False

        mock_instance = MagicMock()
        mock_instance.beparams = {"vcpus": 1, "memory": 1024}

        rapi_client.instance_service.get_instance_names.return_value = ["myinstance"]
        rapi_client.instance_service.get_instance.return_value = mock_instance

        monkeypatch.setattr(
            gnt_instance,
            "dict_diff",
            lambda a, b, exclude: {},
        )

        with pytest.raises(AnsibleExitJson) as exc:
            gnt_instance.ensure_present(module, client_wrapper)

        result = exc.value.kwargs
        rapi_client.instance_service.modify_instance.assert_not_called()
        assert result["changed"] is False
        assert result["msg"] == "Instance myinstance already exists."


class TestEnsureAbsentFunction:
    def test_ensure_absent_instance_exists_check_mode(
        self, module: AnsibleModule, client_wrapper: ClientWrapper, rapi_client
    ):
        module.params = {
            "rapi_address": "mycluster:409",
            "rapi_username": "asdd",
            "rapi_ssl_verify": False,
            "rapi_password": "sdf",
            "instance_name": "removed-instance",
        }
        module.check_mode = True

        rapi_client.instance_service.get_instance_names.return_value = []
        rapi_client.instance_service.delete_instance.return_value = None

        with pytest.raises(AnsibleExitJson) as exc:
            gnt_instance.ensure_absent(module, client_wrapper)

        result = exc.value.kwargs
        rapi_client.instance_service.delete_instance.assert_not_called()
        assert result["changed"] is False
        assert result["msg"] == "Instance removed-instance is already removed."

    def test_ensure_absent_instance_exists(
        self, module: AnsibleModule, client_wrapper: ClientWrapper, rapi_client
    ):
        module.params = {
            "rapi_address": "mycluster:409",
            "rapi_username": "asdd",
            "rapi_ssl_verify": False,
            "rapi_password": "sdf",
            "instance_name": "myinstance",
            "job_poll": True,
            "poll_timeout": 30,
            "poll_interval": 1,
        }

        rapi_client.instance_service.get_instance_names.return_value = ["myinstance"]
        rapi_client.instance_service.delete_instance.return_value = 123
        rapi_client.job_service.wait_for_job.return_value = Job(
            id=123,
            status=JOB_STATUS_SUCCESS,
            ops=[],
            summary=[],
            opstatus=[],
            opresult=[],
        )

        with pytest.raises(AnsibleExitJson) as exc:
            gnt_instance.ensure_absent(module, client_wrapper)

        result = exc.value.kwargs
        rapi_client.instance_service.delete_instance.assert_called_once_with(
            instance_name="myinstance"
        )
        assert result["changed"] is True
        assert result["msg"] == "Instance myinstance removed. Job ID: 123"


class TestGntInstanceModule:
    def test_required_args_missing(self, set_module_args, capsys, get_json_output):
        set_module_args({})
        with pytest.raises(SystemExit):
            gnt_instance.main()

        result = get_json_output(capsys)
        assert result["failed"] is True
        assert "missing required arguments" in result["msg"]

    def test_unknown_state(self, set_module_args, capsys, get_json_output):
        set_module_args(
            {
                "rapi_address": "mycluster:409",
                "rapi_username": "asdd",
                "rapi_port": 123,
                "rapi_ssl_verify": False,
                "rapi_password": "sdf",
                "instance_name": "myinstance",
                "state": "unknown",
            }
        )

        with pytest.raises(SystemExit):
            gnt_instance.main()

        result = get_json_output(capsys)
        assert result["failed"] is True
        assert "value of state must be one of" in result["msg"]
