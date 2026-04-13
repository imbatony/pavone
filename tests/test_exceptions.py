"""pavone/core/exceptions.py 的单元测试。"""

from pavone.core.exceptions import (
    ConfigError,
    DownloadError,
    ExtractError,
    MetadataError,
    NetworkError,
    PavoneError,
    PluginError,
)


class TestPavoneErrorHierarchy:
    """验证异常层级继承关系。"""

    def test_all_subclasses_inherit_pavone_error(self) -> None:
        subclasses = [
            NetworkError,
            DownloadError,
            ExtractError,
            PluginError,
            ConfigError,
            MetadataError,
        ]
        for cls in subclasses:
            instance = cls("test")
            assert isinstance(instance, PavoneError)
            assert isinstance(instance, Exception)

    def test_pavone_error_message(self) -> None:
        err = PavoneError("something went wrong")
        assert err.message == "something went wrong"
        assert str(err) == "something went wrong"

    def test_pavone_error_empty_message(self) -> None:
        err = PavoneError()
        assert err.message == ""
        assert str(err) == ""

    def test_subclass_message_preserved(self) -> None:
        err = NetworkError("连接超时")
        assert err.message == "连接超时"
        assert str(err) == "连接超时"

    def test_exception_can_be_raised_and_caught(self) -> None:
        try:
            raise NetworkError("timeout")
        except PavoneError as e:
            assert str(e) == "timeout"
        else:
            raise AssertionError("PavoneError was not caught")

    def test_each_subclass_is_distinct(self) -> None:
        """确保不同异常类型不会互相捕获。"""
        try:
            raise ConfigError("bad config")
        except NetworkError:
            raise AssertionError("ConfigError should not be caught as NetworkError")
        except ConfigError:
            pass  # expected
