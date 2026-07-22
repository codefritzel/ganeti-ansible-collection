import pytest
from ansible.module_utils.basic import AnsibleModule
from client.models.job import JOB_STATUS_ERROR, JOB_STATUS_SUCCESS, Job
from client.models.network import Network
from unit.ansible_exception import AnsibleExitJson, AnsibleFailJson

from plugins.module_utils.client_wrapper import ClientWrapper
from plugins.modules import gnt_network


def make_network(
    network: str = "10.0.0.0/24",
    gateway: str = "10.0.0.1",
    mac_prefix: str = "aa:00:00",
    network6=None,
    gateway6=None,
):
    return Network(
        name="prod-net",
        uuid="uuid-1",
        network=network,
        gateway=gateway,
        mac_prefix=mac_prefix,
        free_count=100,
        reserved_count=0,
        map="",
        group_list=[],
        external_reservations="",
        network6=network6,
        gateway6=gateway6,
    )


class TestEnsurePresentFunction:
    def test_ensure_present_network_exists(
        self,
        module: AnsibleModule,
        client_wrapper: ClientWrapper,
        rapi_client,
        monkeypatch,
    ):
        module.params = {
            "network_name": "prod-net",
            "network": "10.0.0.0/24",
            "gateway": "10.0.0.1",
            "network6": None,
            "gateway6": None,
            "mac_prefix": "aa:00:00",
        }

        monkeypatch.setattr(client_wrapper, "check_network_exists", lambda name: True)
        rapi_client.network_service.get_network.return_value = make_network()

        with pytest.raises(AnsibleExitJson) as exc:
            gnt_network.ensure_present(module, client_wrapper)

        result = exc.value.kwargs
        rapi_client.network_service.create_network.assert_not_called()
        rapi_client.network_service.modify_network.assert_not_called()
        assert result["changed"] is False
        assert result["msg"] == "Network prod-net already exists."

    def test_ensure_present_network_exists_with_diff_check_mode(
        self,
        module: AnsibleModule,
        client_wrapper: ClientWrapper,
        rapi_client,
        monkeypatch,
    ):
        module.params = {
            "network_name": "prod-net",
            "network": "10.0.1.0/24",
            "gateway": "10.0.1.1",
            "network6": None,
            "gateway6": None,
            "mac_prefix": "aa:00:00",
        }
        module.check_mode = True

        monkeypatch.setattr(client_wrapper, "check_network_exists", lambda name: True)
        rapi_client.network_service.get_network.return_value = make_network()

        with pytest.raises(AnsibleExitJson) as exc:
            gnt_network.ensure_present(module, client_wrapper)

        result = exc.value.kwargs
        rapi_client.network_service.modify_network.assert_not_called()
        assert result["changed"] is True
        assert result["msg"] == "Network prod-net would be modified."

    def test_ensure_present_network_exists_with_diff_successful_modification(
        self,
        module: AnsibleModule,
        client_wrapper: ClientWrapper,
        rapi_client,
        monkeypatch,
    ):
        module.params = {
            "network_name": "prod-net",
            "network": "10.0.1.0/24",
            "gateway": "10.0.1.1",
            "network6": None,
            "gateway6": None,
            "mac_prefix": "aa:00:00",
            "job_poll": True,
            "poll_timeout": 30,
            "poll_interval": 1,
        }

        monkeypatch.setattr(client_wrapper, "check_network_exists", lambda name: True)
        rapi_client.network_service.get_network.return_value = make_network()
        rapi_client.network_service.modify_network.return_value = 456
        rapi_client.job_service.wait_for_job.return_value = Job(
            id=456,
            status=JOB_STATUS_SUCCESS,
            ops=[],
            summary=[],
            opstatus=[],
            opresult=[],
        )

        with pytest.raises(AnsibleExitJson) as exc:
            gnt_network.ensure_present(module, client_wrapper)

        result = exc.value.kwargs
        rapi_client.network_service.modify_network.assert_called_once_with(
            "prod-net", network="10.0.1.0/24", gateway="10.0.1.1"
        )
        assert result["changed"] is True
        assert result["msg"] == "Network prod-net modified. Job ID: 456."
        assert result["job"]["id"] == 456

    def test_ensure_present_network_not_exists_check_mode(
        self,
        module: AnsibleModule,
        client_wrapper: ClientWrapper,
        rapi_client,
        monkeypatch,
    ):
        module.params = {
            "network_name": "prod-net",
            "network": "10.0.0.0/24",
            "gateway": "10.0.0.1",
            "network6": None,
            "gateway6": None,
            "mac_prefix": None,
        }
        module.check_mode = True

        monkeypatch.setattr(client_wrapper, "check_network_exists", lambda name: False)

        with pytest.raises(AnsibleExitJson) as exc:
            gnt_network.ensure_present(module, client_wrapper)

        result = exc.value.kwargs
        rapi_client.network_service.create_network.assert_not_called()
        assert result["changed"] is True
        assert result["msg"] == "Network prod-net would be created."

    def test_ensure_present_network_not_exists_job_successful(
        self,
        module: AnsibleModule,
        client_wrapper: ClientWrapper,
        rapi_client,
        monkeypatch,
    ):
        module.params = {
            "network_name": "prod-net",
            "network": "10.0.0.0/24",
            "gateway": "10.0.0.1",
            "network6": "2001:db8::/64",
            "gateway6": "2001:db8::1",
            "mac_prefix": "aa:00:00",
            "job_poll": True,
            "poll_timeout": 30,
            "poll_interval": 1,
        }

        monkeypatch.setattr(client_wrapper, "check_network_exists", lambda name: False)
        rapi_client.network_service.create_network.return_value = 123
        rapi_client.job_service.wait_for_job.return_value = Job(
            id=123,
            status=JOB_STATUS_SUCCESS,
            ops=[],
            summary=[],
            opstatus=[],
            opresult=[],
        )

        with pytest.raises(AnsibleExitJson) as exc:
            gnt_network.ensure_present(module, client_wrapper)

        rapi_client.network_service.create_network.assert_called_once()
        new_network = rapi_client.network_service.create_network.call_args.kwargs[
            "new_network"
        ]
        assert new_network.network_name == "prod-net"
        assert new_network.network == "10.0.0.0/24"
        assert new_network.gateway == "10.0.0.1"
        assert new_network.network6 == "2001:db8::/64"
        assert new_network.gateway6 == "2001:db8::1"
        assert new_network.mac_prefix == "aa:00:00"

        result = exc.value.kwargs
        assert result["changed"] is True
        assert result["msg"] == "Network prod-net created."
        assert result["job"]["id"] == 123

    def test_ensure_present_network_not_exists_job_error(
        self,
        module: AnsibleModule,
        client_wrapper: ClientWrapper,
        rapi_client,
        monkeypatch,
    ):
        module.params = {
            "network_name": "prod-net",
            "network": "10.0.0.0/24",
            "gateway": "10.0.0.1",
            "network6": None,
            "gateway6": None,
            "mac_prefix": None,
            "job_poll": True,
            "poll_timeout": 30,
            "poll_interval": 1,
        }

        monkeypatch.setattr(client_wrapper, "check_network_exists", lambda name: False)
        rapi_client.network_service.create_network.return_value = 123
        rapi_client.job_service.wait_for_job.return_value = Job(
            id=123,
            status=JOB_STATUS_ERROR,
            ops=[],
            summary=[],
            opstatus=[],
            opresult=[],
        )

        with pytest.raises(AnsibleFailJson) as exc:
            gnt_network.ensure_present(module, client_wrapper)

        rapi_client.network_service.create_network.assert_called_once()
        result = exc.value.kwargs
        assert result["changed"] is False
        assert result["msg"] == "Job 123 was not successful. Status: error"

    def test_ensure_present_network_not_exists_without_job_poll(
        self,
        module: AnsibleModule,
        client_wrapper: ClientWrapper,
        rapi_client,
        monkeypatch,
    ):
        module.params = {
            "network_name": "prod-net",
            "network": "10.0.0.0/24",
            "gateway": "10.0.0.1",
            "network6": None,
            "gateway6": None,
            "mac_prefix": None,
            "job_poll": False,
        }

        monkeypatch.setattr(client_wrapper, "check_network_exists", lambda name: False)
        rapi_client.network_service.create_network.return_value = 123

        with pytest.raises(AnsibleExitJson) as exc:
            gnt_network.ensure_present(module, client_wrapper)

        rapi_client.network_service.create_network.assert_called_once()
        rapi_client.job_service.wait_for_job.assert_not_called()

        result = exc.value.kwargs
        assert result["changed"] is True
        assert result["msg"] == "Job 123 started."
        assert result["job_id"] == 123


class TestEnsureAbsentFunction:
    def test_ensure_absent_network_already_removed(
        self,
        module: AnsibleModule,
        client_wrapper: ClientWrapper,
        rapi_client,
        monkeypatch,
    ):
        module.params = {
            "network_name": "prod-net",
        }

        monkeypatch.setattr(client_wrapper, "check_network_exists", lambda name: False)

        with pytest.raises(AnsibleExitJson) as exc:
            gnt_network.ensure_absent(module, client_wrapper)

        result = exc.value.kwargs
        rapi_client.network_service.delete_network.assert_not_called()
        assert result["changed"] is False
        assert result["msg"] == "Network prod-net already removed."

    def test_ensure_absent_network_exists_check_mode(
        self,
        module: AnsibleModule,
        client_wrapper: ClientWrapper,
        rapi_client,
        monkeypatch,
    ):
        module.params = {
            "network_name": "prod-net",
        }
        module.check_mode = True

        monkeypatch.setattr(client_wrapper, "check_network_exists", lambda name: True)

        with pytest.raises(AnsibleExitJson) as exc:
            gnt_network.ensure_absent(module, client_wrapper)

        result = exc.value.kwargs
        rapi_client.network_service.delete_network.assert_not_called()
        assert result["changed"] is True
        assert result["msg"] == "Network prod-net would be removed."

    def test_ensure_absent_network_exists_job_successful(
        self,
        module: AnsibleModule,
        client_wrapper: ClientWrapper,
        rapi_client,
        monkeypatch,
    ):
        module.params = {
            "network_name": "prod-net",
            "job_poll": True,
            "poll_timeout": 30,
            "poll_interval": 1,
        }

        monkeypatch.setattr(client_wrapper, "check_network_exists", lambda name: True)
        rapi_client.network_service.delete_network.return_value = 456
        rapi_client.job_service.wait_for_job.return_value = Job(
            id=456,
            status=JOB_STATUS_SUCCESS,
            ops=[],
            summary=[],
            opstatus=[],
            opresult=[],
        )

        with pytest.raises(AnsibleExitJson) as exc:
            gnt_network.ensure_absent(module, client_wrapper)

        result = exc.value.kwargs
        rapi_client.network_service.delete_network.assert_called_once_with(
            network_name="prod-net"
        )
        assert result["changed"] is True
        assert result["msg"] == "Network prod-net removed."
        assert result["job"]["id"] == 456

    def test_ensure_absent_network_exists_without_job_poll(
        self,
        module: AnsibleModule,
        client_wrapper: ClientWrapper,
        rapi_client,
        monkeypatch,
    ):
        module.params = {
            "network_name": "prod-net",
            "job_poll": False,
        }

        monkeypatch.setattr(client_wrapper, "check_network_exists", lambda name: True)
        rapi_client.network_service.delete_network.return_value = 456

        with pytest.raises(AnsibleExitJson) as exc:
            gnt_network.ensure_absent(module, client_wrapper)

        rapi_client.network_service.delete_network.assert_called_once_with(
            network_name="prod-net"
        )
        rapi_client.job_service.wait_for_job.assert_not_called()

        result = exc.value.kwargs
        assert result["changed"] is True
        assert result["msg"] == "Job 456 started."
        assert result["job_id"] == 456


class TestGntNetworkModule:
    def test_required_args_missing(self, set_module_args, capsys, get_json_output):
        set_module_args({})
        with pytest.raises(SystemExit):
            gnt_network.main()

        result = get_json_output(capsys)
        assert result["failed"] is True
        assert "missing required arguments" in result["msg"]

    def test_unknown_state(self, set_module_args, capsys, get_json_output):
        set_module_args(
            {
                "rapi_address": "mycluster:409",
                "rapi_port": 123,
                "rapi_username": "asdd",
                "ssl_verify": False,
                "rapi_password": "sdf",
                "network_name": "prod-net",
                "state": "unknown",
            }
        )

        with pytest.raises(SystemExit):
            gnt_network.main()

        result = get_json_output(capsys)
        assert result["failed"] is True
        assert "value of state must be one of" in result["msg"]
