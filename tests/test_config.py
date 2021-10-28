def test_config_load(config):
    files = config["files"]

    assert files

    for spec in files.values():
        assert spec["filename"]
        assert spec["pattern"]
