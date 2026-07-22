import json
from unittest.mock import MagicMock

import pytest
from _pytest.monkeypatch import MonkeyPatch
from ansible.module_utils import basic
from ansible.module_utils.common.text.converters import to_bytes

from plugins.module_utils.client_wrapper import ClientWrapper
from unit.ansible_exception import AnsibleExitJson, AnsibleFailJson


def exit_json(*args, **kwargs):
    if "changed" not in kwargs:
        kwargs["changed"] = False

    raise AnsibleExitJson(*args, **kwargs)


def fail_json(*args, **kwargs):
    kwargs["failed"] = True
    raise AnsibleFailJson(*args, **kwargs)


@pytest.fixture
def set_module_args():
    def _set_module_args(args):
        args = json.dumps({"ANSIBLE_MODULE_ARGS": args})
        basic._ANSIBLE_ARGS = to_bytes(args)

        # use the legacy profile as ansible's testing helpers do
        basic._ANSIBLE_PROFILE = "legacy"

    return _set_module_args


@pytest.fixture
def get_json_output():
    def _get_json_output(capsys):
        captured = capsys.readouterr()
        return json.loads(captured.out)

    return _get_json_output


@pytest.fixture
def module(monkeypatch: MonkeyPatch) -> MagicMock:
    module = MagicMock()
    module.check_mode = False
    module.params = {}  # Initialisiere params als echtes Dictionary
    monkeypatch.setattr(module, "exit_json", exit_json)
    monkeypatch.setattr(module, "fail_json", fail_json)
    return module


@pytest.fixture
def rapi_client() -> MagicMock:
    return MagicMock()


@pytest.fixture
def client_wrapper(
    monkeypatch: MonkeyPatch, module: MagicMock, rapi_client: MagicMock
) -> ClientWrapper:
    # Patch _initialize_client BEVOR ClientWrapper erstellt wird
    monkeypatch.setattr(ClientWrapper, "_initialize_client", lambda self: None)

    wrapper = ClientWrapper(module)
    wrapper._client = rapi_client

    return wrapper


# @pytest.fixture(autouse=True)
# def patch_ansible_exit(monkeypatch: MonkeyPatch):
#    """Patch fail_json and exit_json for all test calls"""
#    monkeypatch.setattr("ansible.module_utils.basic.AnsibleModule.exit_json", exit_json)
#    monkeypatch.setattr("ansible.module_utils.basic.AnsibleModule.fail_json", fail_json)
