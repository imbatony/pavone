"""pavone/core/exit_codes.py 的单元测试。"""

from pavone.core.exit_codes import ExitCode


class TestExitCode:
    """验证退出码常量值正确且无重复。"""

    def test_exit_code_values(self) -> None:
        assert ExitCode.SUCCESS == 0
        assert ExitCode.GENERAL_ERROR == 1
        assert ExitCode.USAGE_ERROR == 2
        assert ExitCode.NETWORK_ERROR == 3
        assert ExitCode.CONFIG_ERROR == 4

    def test_no_duplicate_values(self) -> None:
        values = [
            ExitCode.SUCCESS,
            ExitCode.GENERAL_ERROR,
            ExitCode.USAGE_ERROR,
            ExitCode.NETWORK_ERROR,
            ExitCode.CONFIG_ERROR,
        ]
        assert len(values) == len(set(values)), "Exit code values must be unique"
