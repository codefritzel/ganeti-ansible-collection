import pytest

from plugins.modules import gnt_job_info


class TestGntJobInfoModule:
    def test_required_args_missing(self, set_module_args, capsys, get_json_output):
        set_module_args({})
        with pytest.raises(SystemExit):
            gnt_job_info.main()

        result = get_json_output(capsys)
        assert result["failed"] is True
        assert "missing required arguments" in result["msg"]
