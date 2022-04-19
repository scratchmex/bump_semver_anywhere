from pytest_mock.plugin import MockerFixture

from manver.app import App


def test_git_stage_and_commit(mocker: MockerFixture, patch_app):
    app = App()

    assert app.vcs

    cm = app.bump("patch")

    mocked = mocker.patch.object(app.vcs, "_run_cmd", return_value=None)

    app.vcs.stage()

    for file in app.vcs.files:
        cmd = app.vcs._get_stage_cmd() + [file]
        mocked.assert_any_call(cmd)

    mocked.reset_mock()

    app.vcs.commit(cm)

    mocked.assert_called_once_with(app.vcs._get_commit_cmd() + [cm])
