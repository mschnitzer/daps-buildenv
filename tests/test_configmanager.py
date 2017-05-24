import dapsenv.configmanager as configmanager
import os.path
import pytest
from __utils__ import make_tmp_file
from dapsenv.exceptions import ConfigFileCreationPermissionErrorException, \
                               ConfigFileAlreadyExistsException
from unittest.mock import patch

test_data_dir = "{}/data".format(os.path.dirname(os.path.realpath(__file__)))

# it returns a value of a property from a configuration file
input_data = [
    (
        "own",
        "{}/own-config.conf".format(test_data_dir),
        "test",
        "some cool text"
    ),
    (
        "global",
        "{}/global-config.conf".format(test_data_dir),
        "prop",
        "my cool value"
    ),
    (
        "user",
        "{}/user-config.conf".format(test_data_dir),
        "abc",
        "def"
    ),
]

@patch("dapsenv.configmanager.get_global_config_path")
@patch("dapsenv.configmanager.get_user_config_path")
@pytest.mark.parametrize("config_type,config_path,prop,expect", input_data)
def test_get(mock_get_user_config_path, mock_get_global_config_path, config_type, config_path,
    prop, expect):

    mock_get_global_config_path.return_value = config_path
    mock_get_user_config_path.return_value = config_path

    value = configmanager.get_prop(prop, config_type, config_path)
    assert value == expect

# it sets values for a property in a config file
input_data = [
    (
        "abc",
        "hello world",
        "# that's a comment\nsomething_to_update=abc\nabc=hello world",
        "own"
    ),
    (
        "some_key",
        "testxyz",
        "# that's a comment\nsomething_to_update=abc\nsome_key=testxyz",
        "global"
    ),
    (
        "something_to_update",
        "new_content",
        "# that's a comment\nsomething_to_update=new_content",
        "user"
    ),
]

@patch("dapsenv.configmanager.get_global_config_path")
@patch("dapsenv.configmanager.get_user_config_path")
@pytest.mark.parametrize("prop,value,expected_content,config_type", input_data)
def test_set(mock_get_user_config_path, mock_get_global_config_path, prop, value,
    expected_content, config_type, tmpdir):

    tmp_file = make_tmp_file("set-test.conf", tmpdir)
    tmp_file_path = str(tmp_file.realpath())

    mock_get_global_config_path.return_value = tmp_file_path
    mock_get_user_config_path.return_value = tmp_file_path

    configmanager.set_prop(prop, value, config_type, tmp_file_path)

    content = ""
    with open(tmp_file_path, "r") as f:
        content = f.read()

    assert content == expected_content

# it returns the correct paths for all 3 types of config files
input_data = [
    (
        "own",
        "/tmp/something/bla.conf",
        "/tmp/something/bla.conf"
    ),
    (
        "user",
        "",
        "{}/.dapsenv/dapsenv.conf".format(os.path.expanduser("~")),
    ),
    (
        "global",
        "",
        "/etc/dapsenv/dapsenv.conf"
    )
]

@pytest.mark.parametrize("config_type,config_path,expected_path", input_data)
def test_get_config_path(config_type,config_path,expected_path):
    assert configmanager.get_config_path(config_type,config_path) == expected_path

# it parses multiple config files and merges the content together
def test_parse_config():
    config_files = [
        "{}/merge-test1.conf".format(test_data_dir),
        "{}/merge-test2.conf".format(test_data_dir),
        "{}/merge-test3.conf".format(test_data_dir)
    ]

    expected = {
        "prop": "my cool value",
        "merge_test": "content2",
        "abc": "def",
        "test": "some cool text",
        "merge_test2": "content1"
    }

    assert configmanager.parse_config(config_files) == expected

# it tests if a config file can be created at a given path
def test_generate_config(tmpdir_factory):
    path = str(tmpdir_factory.getbasetemp())
    file_name = "{}/dapsenv.conf".format(path)

    assert os.path.exists(file_name) is False
    configmanager.generate_config(path)
    assert os.path.exists(file_name) is True

# it fails if a configuration file could not be created due to invalid permissions
def test_generate_config_permission_error():
    assert os.path.exists("/dapsenv.conf") is False

    with pytest.raises(ConfigFileCreationPermissionErrorException):
        configmanager.generate_config("/")

# it fails if a configuration file could not be created cause there is already
# a config file with the same name
def test_generate_config_already_exists(tmpdir_factory):
    path = str(tmpdir_factory.getbasetemp())
    file_name = "{}/dapsenv.conf".format(path)

    if not os.path.exists(file_name):
        configmanager.generate_config(path)

    assert os.path.exists(file_name) is True

    with pytest.raises(ConfigFileAlreadyExistsException):
        configmanager.generate_config(path)
