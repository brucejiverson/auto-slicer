
# tests/test_octopi_integration.py
import pytest
from unittest.mock import patch, MagicMock
from auto_slicer.octopi_integration import (
    initialize_client,
    is_print_job_active,
    get_printer_info,
    add_set_to_continous_print,
    get_continuous_print_state
)


@pytest.mark.asyncio
async def test_initialize_client():
    with patch('octorest.OctoRest') as mock_octorest:
        mock_client = MagicMock()
        mock_octorest.return_value = mock_client

        client = await initialize_client()
        assert client == mock_client


@pytest.mark.asyncio
async def test_is_print_job_active():
    with patch('auto_slicer.octopi_integration.client') as mock_client:
        mock_client.printer.return_value = {
            'state': {'flags': {'printing': False}}
        }
        result = await is_print_job_active()
        assert result is False


# test continue print functions for real

def test_continuous_print():
    get_continuous_print_state()
    add_set_to_continous_print(
        path,
        sd=False,
        count=1,
        jobName="Job",
        jobDraft=True,
        timeout=10
    )


if __name__ == "__main__":
    import asyncio
    asyncio.run(initialize_client())
    asyncio.run(get_printer_info())
    asyncio.run(get_files())
