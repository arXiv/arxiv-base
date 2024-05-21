import unittest
from unittest.mock import patch, MagicMock
from fastly.api.purge_api import PurgeApi

from arxiv.integration.fastly.purge import purge_fastly_keys

class TestPurgeFastlyKeys(unittest.TestCase):
    @patch('arxiv.integration.fastly.purge.PurgeApi')
    @patch('arxiv.integration.fastly.purge.fastly.ApiClient')
    def test_purge_single_key(self, MockApiClient, MockPurgeApi: PurgeApi):
        mock_api_instance:PurgeApi = MockPurgeApi.return_value
        mock_api_instance.purge_tag = MagicMock()

        purge_fastly_keys('test', "export.arxiv.org")

        mock_api_instance.purge_tag.assert_called_once_with(
            service_id="hCz5jlkWV241zvUN0aWxg2",
            surrogate_key='test',
            fastly_soft_purge=1
        )


    @patch('arxiv.integration.fastly.purge.PurgeApi')
    @patch('arxiv.integration.fastly.purge.fastly.ApiClient')
    def test_purge_multiple_keys(self, MockApiClient, MockPurgeApi: PurgeApi):
        mock_api_instance:PurgeApi = MockPurgeApi.return_value
        mock_api_instance.bulk_purge_tag = MagicMock()

        keys = ['key1', 'key2']
        purge_fastly_keys(keys)

        mock_api_instance.bulk_purge_tag.assert_called_once_with(
            service_id="umpGzwE2hXfa2aRXsOQXZ4",
            purge_response= {'surrogate_keys':keys},
            fastly_soft_purge=1
        )


    @patch('arxiv.integration.fastly.purge.PurgeApi')
    @patch('arxiv.integration.fastly.purge.fastly.ApiClient')
    @patch('arxiv.integration.fastly.purge.MAX_PURGE_KEYS', 3)
    def test_purge_over_max_keys(self, MockApiClient, MockPurgeApi: PurgeApi):
        mock_api_instance:PurgeApi = MockPurgeApi.return_value
        mock_api_instance.bulk_purge_tag = MagicMock()

        keys = ['1', '2', '3', '4','5','6','7']
        purge_fastly_keys(keys)
        calls = [
            unittest.mock.call(
                service_id="umpGzwE2hXfa2aRXsOQXZ4",
                purge_response= {'surrogate_keys':['1','2','3']},
                fastly_soft_purge=1
            ),
                        unittest.mock.call(
                service_id="umpGzwE2hXfa2aRXsOQXZ4",
                purge_response= {'surrogate_keys':['4','5','6']},
                fastly_soft_purge=1
            ),
                        unittest.mock.call(
                service_id="umpGzwE2hXfa2aRXsOQXZ4",
                purge_response= {'surrogate_keys':['7']},
                fastly_soft_purge=1
            ),
        ]

        mock_api_instance.bulk_purge_tag.assert_has_calls(calls, any_order=True)

