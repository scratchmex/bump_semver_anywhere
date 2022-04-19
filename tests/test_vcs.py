from pytest_mock.plugin import MockerFixture

from manver.app import VersionManager


def test_git_stage_and_commit(mocker: MockerFixture, patch_version_manager):
    app = VersionManager()

    assert app.vcs

    cm = app.bump("patch")

    mocked = mocker.patch.object(app.vcs, "_run_cmd", return_value=None)

    app.vcs.stage(app.config.files)

    for file in app.config.files:
        cmd = app.vcs._get_stage_cmd() + [file]
        mocked.assert_any_call(cmd)

    mocked.reset_mock()

    app.vcs.commit(cm)

    mocked.assert_called_once_with(app.vcs._get_commit_cmd() + [cm])
