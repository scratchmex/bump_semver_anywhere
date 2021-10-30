from pytest_mock.plugin import MockerFixture

from bump_semver_anywhere.app import App


def test_git_stage_and_commit(mocker: MockerFixture, patch_app):
    app = App()

    assert app.vcs

    app.bump("patch")

    assert app.vcs.commit_msg == "release(patch): bump 0.1.0 -> 0.1.1"

    mocked = mocker.patch.object(app.vcs, "_run_cmd", return_value=None)

    app.vcs.stage()

    for file in app.vcs.files:
        cmd = app.vcs._get_stage_cmd() + [file]
        mocked.assert_any_call(cmd)

    mocked.reset_mock()

    app.vcs.commit()

    mocked.assert_called_once_with(app.vcs._get_commit_cmd() + [app.vcs.commit_msg])
