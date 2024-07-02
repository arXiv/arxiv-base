import unittest
from unittest.mock import patch, MagicMock
from datetime import date
from fastly.api.purge_api import PurgeApi

from arxiv.identifier import Identifier
from arxiv.integration.fastly.purge import purge_fastly_keys, _purge_category_change, purge_cache_for_paper
from arxiv.integration.fastly.headers import add_surrogate_key

#tests for the purge keys utility function
class TestPurgeFastlyKeys(unittest.TestCase):
    @patch('arxiv.integration.fastly.purge.PurgeApi')
    @patch('arxiv.integration.fastly.purge.fastly.ApiClient')
    def test_purge_single_key(self, MockApiClient, MockPurgeApi: PurgeApi):
        mock_api_instance:PurgeApi = MockPurgeApi.return_value
        mock_api_instance.purge_tag = MagicMock()

        purge_fastly_keys('test', "export.arxiv.org")

        mock_api_instance.purge_tag.assert_called_once_with(
            service_id="hCz5jlkWV241zvUN0aWxg2",
            surrogate_key='test'
        )

    @patch('arxiv.integration.fastly.purge.PurgeApi')
    @patch('arxiv.integration.fastly.purge.fastly.ApiClient')
    def test_purge_single_key(self, MockApiClient, MockPurgeApi: PurgeApi):
        mock_api_instance:PurgeApi = MockPurgeApi.return_value
        mock_api_instance.purge_tag = MagicMock()

        purge_fastly_keys('test', "export.arxiv.org", True)

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
            purge_response= {'surrogate_keys':keys}
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
                purge_response= {'surrogate_keys':['1','2','3']}
            ),
                        unittest.mock.call(
                service_id="umpGzwE2hXfa2aRXsOQXZ4",
                purge_response= {'surrogate_keys':['4','5','6']}
            ),
                        unittest.mock.call(
                service_id="umpGzwE2hXfa2aRXsOQXZ4",
                purge_response= {'surrogate_keys':['7']}
            ),
        ]

        mock_api_instance.bulk_purge_tag.assert_has_calls(calls, any_order=True)


#tests for adding surrogate keys helper function
def test_empty_keys():
        headers = {}
        keys = []
        expected = {"Surrogate-Key": ""}
        assert add_surrogate_key(headers, keys)== expected
        
def test_add_keys():
    headers = {"Surrogate-Key": "key1"}
    keys = ["key2", "key3"]
    expected = {"Surrogate-Key": "key1 key2 key3"}
    assert expected == add_surrogate_key(headers, keys)
    
def test_duplicate_keys():
    headers = {"Surrogate-Key": "key1 key2"}
    keys = ["key2", "key3", "key3"]
    expected = {"Surrogate-Key": "key1 key2 key3"}
    assert expected== add_surrogate_key(headers, keys)

def test_keys_with_spaces():
    headers = {"Surrogate-Key": " key1 "}
    keys = [" key2 "]
    expected = {"Surrogate-Key": "key1 key2"}
    assert expected== add_surrogate_key(headers, keys)

def test_other_headers():
    headers = {"A Header": "nifty info"}
    keys = [" key2 "]
    expected = {"A Header": "nifty info", "Surrogate-Key": "key2"}
    assert expected== add_surrogate_key(headers, keys)

#tests for finding all /year and /list pages to purge for a paper
@patch('arxiv.integration.fastly.purge._get_category_and_date')
@patch('arxiv.integration.fastly.purge.date')
def test_purge_category_change_basic(mockToday,mockDBQuery):
   
   #old
    mockToday.today.return_value=date(2024,1,1)
    mockDBQuery.return_value=("cs.LG", date(2010,1,1))
    result=_purge_category_change(Identifier('1001.5678'))
    expected=["list-2010-01-cs.LG", "list-2010-cs.LG", "list-2010-01-cs", "list-2010-cs"]
    assert sorted(result)==sorted(expected)

    #recent
    mockToday.today.return_value=date(2010,2,3)
    mockDBQuery.return_value=("cs.LG", date(2010,1,29))
    result=_purge_category_change(Identifier('1001.5678'))
    expected=["list-2010-01-cs.LG", "list-2010-cs.LG", "list-2010-01-cs", "list-2010-cs", "list-recent-cs", "list-recent-cs.LG"]
    assert sorted(result)==sorted(expected)
   
    #new
    mockToday.today.return_value=date(2010,2,1)
    mockDBQuery.return_value=("cs.LG", date(2010,1,29))
    result=_purge_category_change(Identifier('1001.5678'))
    expected=["list-2010-01-cs.LG", "list-2010-cs.LG", "list-2010-01-cs", "list-2010-cs", "list-recent-cs", "list-recent-cs.LG", "list-new-cs", "list-new-cs.LG"]
    assert sorted(result)==sorted(expected)

@patch('arxiv.integration.fastly.purge._get_category_and_date')
@patch('arxiv.integration.fastly.purge.date')
def test_purge_category_change_alias_cats(mockToday,mockDBQuery):
   
   #non cannonical categories listed
    mockToday.today.return_value=date(2024,1,1)
    mockDBQuery.return_value=("solv-int cs.SY", date(2010,1,1))
    result=_purge_category_change(Identifier('1001.5678'))
    expected=["list-2010-01-nlin.SI", "list-2010-nlin.SI", "list-2010-01-nlin", "list-2010-nlin","list-2010-01-eess.SY", "list-2010-eess.SY", "list-2010-01-eess", "list-2010-eess", "list-2010-01-cs", "list-2010-cs" ]
    assert sorted(result)==sorted(expected)

    #find archives of unlisted noncanonical categories
    mockToday.today.return_value=date(2024,1,1)
    mockDBQuery.return_value=("nlin.SI eess.SY", date(2010,1,1))
    result=_purge_category_change(Identifier('1001.5678'))
    expected=["list-2010-01-nlin.SI", "list-2010-nlin.SI", "list-2010-01-nlin", "list-2010-nlin","list-2010-01-eess.SY", "list-2010-eess.SY", "list-2010-01-eess", "list-2010-eess", "list-2010-01-cs", "list-2010-cs" ]
    assert sorted(result)==sorted(expected)

@patch('arxiv.integration.fastly.purge._get_category_and_date')
@patch('arxiv.integration.fastly.purge.date')
def test_purge_category_change_remove_cats(mockToday,mockDBQuery):
   #basic remove cat
    mockToday.today.return_value=date(2024,1,1)
    mockDBQuery.return_value=("cs.LG", date(2010,1,1))
    result=_purge_category_change(Identifier('1001.5678'),"cs.LG cs.DC")
    expected=["list-2010-01-cs.LG", "list-2010-cs.LG", "list-2010-01-cs", "list-2010-cs", "list-2010-01-cs.DC", "list-2010-cs.DC"]
    assert sorted(result)==sorted(expected)

    #remove archive
    mockToday.today.return_value=date(2024,1,1)
    mockDBQuery.return_value=("cs.LG", date(2010,1,1))
    result=_purge_category_change(Identifier('1001.5678'),"cs.LG hep-lat")
    expected=["list-2010-01-cs.LG", "list-2010-cs.LG", "list-2010-01-cs", "list-2010-cs", "list-2010-01-hep-lat", "list-2010-hep-lat", "year-hep-lat-2010"]
    assert sorted(result)==sorted(expected)

    #remove archive of alias
    mockToday.today.return_value=date(2024,1,1)
    mockDBQuery.return_value=("cs.LG", date(2010,1,1))
    result=_purge_category_change(Identifier('1001.5678'),"cs.LG math.ST")
    expected=["list-2010-01-cs.LG", "list-2010-cs.LG", "list-2010-01-cs", "list-2010-cs", "list-2010-01-math.ST", "list-2010-math.ST", "list-2010-01-math", "list-2010-math", "year-math-2010", "list-2010-01-stat", "list-2010-stat", "year-stat-2010"]
    assert sorted(result)==sorted(expected)

@patch('arxiv.integration.fastly.purge._get_category_and_date')
@patch('arxiv.integration.fastly.purge.date')
def test_purge_category_change_add_cats(mockToday,mockDBQuery):
   #basic add cat
    mockToday.today.return_value=date(2024,1,1)
    mockDBQuery.return_value=("cs.LG cs.DC", date(2010,1,1))
    result=_purge_category_change(Identifier('1001.5678'),"cs.LG")
    expected=["list-2010-01-cs.LG", "list-2010-cs.LG", "list-2010-01-cs", "list-2010-cs", "list-2010-01-cs.DC", "list-2010-cs.DC"]
    assert sorted(result)==sorted(expected)

    #add archive
    mockToday.today.return_value=date(2024,1,1)
    mockDBQuery.return_value=("cs.LG hep-lat", date(2010,1,1))
    result=_purge_category_change(Identifier('1001.5678'),"cs.LG")
    expected=["list-2010-01-cs.LG", "list-2010-cs.LG", "list-2010-01-cs", "list-2010-cs", "list-2010-01-hep-lat", "list-2010-hep-lat", "year-hep-lat-2010"]
    assert sorted(result)==sorted(expected)

    #add archive of alias
    mockToday.today.return_value=date(2024,1,1)
    mockDBQuery.return_value=("cs.LG math.ST", date(2010,1,1))
    result=_purge_category_change(Identifier('1001.5678'),"cs.LG")
    expected=["list-2010-01-cs.LG", "list-2010-cs.LG", "list-2010-01-cs", "list-2010-cs", "list-2010-01-math.ST", "list-2010-math.ST", "list-2010-01-math", "list-2010-math", "year-math-2010", "list-2010-01-stat", "list-2010-stat", "year-stat-2010"]
    assert sorted(result)==sorted(expected)

@patch('arxiv.integration.fastly.purge._get_category_and_date')
@patch('arxiv.integration.fastly.purge.purge_fastly_keys')
@patch('arxiv.integration.fastly.purge.date')
def test_purge_cache_for_paper(mockToday,mockPurge, mockDBQuery):
    mockToday.today.return_value=date(2024,1,1)
    mockDBQuery.return_value=("cs.LG cs.DC", date(2010,1,1))
    expected_keys=["list-2010-01-cs.LG", "list-2010-cs.LG", "list-2010-01-cs", "list-2010-cs", "list-2010-01-cs.DC", "list-2010-cs.DC", "paper-id-1001.5678"]
    purge_cache_for_paper('1001.5678',"cs.LG")
    actual_keys = mockPurge.call_args[0][0]
    assert sorted(actual_keys) == sorted (expected_keys)