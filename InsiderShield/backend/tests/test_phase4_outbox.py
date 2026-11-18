from unittest.mock import patch

import pytest

from app.worker.tasks import process_outbox_message
def test_process_task_uses_exponential_backoff():
    task = process_outbox_message

    with patch(
        "app.worker.tasks._process_message",
        side_effect=RuntimeError("simulated failure"),
    ), patch.object(
        task,
        "retry",
        side_effect=RuntimeError("retry scheduled"),
    ) as mocked_retry:

        task.push_request(retries=0)

        try:
            with pytest.raises(RuntimeError, match="retry scheduled"):
                task.run("17af9388-e8f7-4791-aa12-737be7c7326d")

            mocked_retry.assert_called_once()
            assert mocked_retry.call_args.kwargs["countdown"] == 2

        finally:
            task.pop_request()
