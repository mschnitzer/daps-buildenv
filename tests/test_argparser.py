#
import pytest
from dapsenv import configmanager
from dapsenv.argparser import ArgParser
from dapsenv.exitcodes import E_INVALID_CLI
from dapsenv.general import __version__


# it exits with exit code 2 if an invalid action/sub-command was specified
def test_parse_exception(monkeypatch):
    monkeypatch.setattr(configmanager, 'get_prop', lambda _: "fake")
    with pytest.raises(SystemExit) as error:
        argparser = ArgParser(["test", "abc", "123"])
        parsed_args = argparser.parse()

    assert error.value.code == E_INVALID_CLI


# it succeeds if a valid command was parsed to the command line
def test_parse_success(monkeypatch):
    monkeypatch.setattr(configmanager, 'get_prop', lambda _: "fake")
    argparser = ArgParser(["config", "--global", "--property", "test"])
    args = argparser.parse()
    assert args['action'] == 'config'
    assert args['global'] == True
    assert args['property'] == 'test'


# it returns the correct version number
def test_return_version(monkeypatch, capsys):
    monkeypatch.setattr(configmanager, 'get_prop', lambda _: "fake")
    with pytest.raises(SystemExit) as error:
        argparser = ArgParser(["--version"])
        parsed_args = argparser.parse()

    out, err = capsys.readouterr()

    assert out == "DAPS Build Environment Version {}\n".format(__version__)
