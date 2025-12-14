import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Prefer test mode to allow stub ChatBox when optional deps are missing
os.environ.setdefault("TOOL_TEST_MODE", "1")

# Ensure ChatSystem modules are importable when running tests from repo root
sys.path.insert(0, os.path.dirname(__file__))

from TOOL import TOOL


def _make_sequence_mock():
    return MagicMock(spec=[
        "append",
        "pop",
        "get_sequence",
        "clear_sequence",
        "id_to_name",
        "input_start_coordinate",
        "get_start_coordinate",
        "search_by_name",
        "get_suggest_category",
        "suggest_for_position",
        "suggest_around",
        "suggest_itinerary_to_sequence",
    ])


def _make_chatbox_mock():
    return MagicMock(spec=["process_input", "clear_conversation"])


class TestTOOL(unittest.TestCase):
    def _create_tool_with_mocks(self):
        seq_mock = _make_sequence_mock()
        chat_mock = _make_chatbox_mock()
        with patch("TOOL.LocationSequence", return_value=seq_mock) as seq_cls, \
             patch("TOOL.ChatBox", return_value=chat_mock) as chat_cls:
            tool = TOOL()
        seq_cls.assert_called_once_with()
        chat_cls.assert_called_once_with(seq_mock)
        return tool, seq_mock, chat_mock

    def test_init_constructs_components(self):
        tool, seq_mock, chat_mock = self._create_tool_with_mocks()
        self.assertIs(tool.sequence, seq_mock)
        self.assertIs(tool.chatbox, chat_mock)

    def test_append_delegates_to_sequence(self):
        tool, seq_mock, _ = self._create_tool_with_mocks()
        tool.append(1, 42)
        seq_mock.append.assert_called_once_with(1, 42)

    def test_pop_delegates_to_sequence(self):
        tool, seq_mock, _ = self._create_tool_with_mocks()
        tool.pop(2)
        seq_mock.pop.assert_called_once_with(2)

    def test_get_sequence_passthrough(self):
        tool, seq_mock, _ = self._create_tool_with_mocks()
        seq_mock.get_sequence.return_value = [1, 2, 3]
        self.assertEqual(tool.get_sequence(), [1, 2, 3])

    def test_clear_sequence_delegates(self):
        tool, seq_mock, _ = self._create_tool_with_mocks()
        tool.clear_sequence()
        seq_mock.clear_sequence.assert_called_once_with()

    def test_id_to_name_passthrough(self):
        tool, seq_mock, _ = self._create_tool_with_mocks()
        seq_mock.id_to_name.return_value = "Name"
        self.assertEqual(tool.id_to_name(7), "Name")
        seq_mock.id_to_name.assert_called_once_with(7)

    def test_start_coordinate_helpers(self):
        tool, seq_mock, _ = self._create_tool_with_mocks()
        tool.input_start_coordinate(10.0, 20.0)
        seq_mock.input_start_coordinate.assert_called_once_with(10.0, 20.0)

        seq_mock.get_start_coordinate.return_value = [10.0, 20.0]
        self.assertEqual(tool.get_start_coordinate(), [10.0, 20.0])
        seq_mock.get_start_coordinate.assert_called_once_with()

    def test_search_by_name_passthrough(self):
        tool, seq_mock, _ = self._create_tool_with_mocks()
        seq_mock.search_by_name.return_value = [5, 6]
        result = tool.search_by_name("park", exact=False, limit=2)
        self.assertEqual(result, [5, 6])
        seq_mock.search_by_name.assert_called_once_with("park", False, 2)

    def test_get_suggest_category_passthrough(self):
        tool, seq_mock, _ = self._create_tool_with_mocks()
        seq_mock.get_suggest_category.return_value = "cafe"
        self.assertEqual(tool.get_suggest_category(), "cafe")
        seq_mock.get_suggest_category.assert_called_once_with()

    def test_suggest_for_position_uses_keywords(self):
        tool, seq_mock, _ = self._create_tool_with_mocks()
        seq_mock.suggest_for_position.return_value = [1, 2]
        result = tool.suggest_for_position(position=3, category="museum", limit=4)
        self.assertEqual(result, [1, 2])
        seq_mock.suggest_for_position.assert_called_once_with(pos=3, category="museum", limit=4)

    def test_suggest_around_passthrough(self):
        tool, seq_mock, _ = self._create_tool_with_mocks()
        seq_mock.suggest_around.return_value = [9]
        result = tool.suggest_around(1.0, 2.0, limit=3, category="park")
        self.assertEqual(result, [9])
        seq_mock.suggest_around.assert_called_once_with(lat=1.0, lon=2.0, limit=3, category="park")

    def test_suggest_itinerary_passthrough(self):
        tool, seq_mock, _ = self._create_tool_with_mocks()
        seq_mock.suggest_itinerary_to_sequence.return_value = [11, 12]
        result = tool.suggest_itinerary_to_sequence(limit=2)
        self.assertEqual(result, [11, 12])
        seq_mock.suggest_itinerary_to_sequence.assert_called_once_with(2)

    def test_process_input_returns_serialized_output(self):
        tool, _, chat_mock = self._create_tool_with_mocks()
        response_mock = MagicMock()
        response_mock.get_json_serializable.return_value = {"msg": "ok"}
        chat_mock.process_input.return_value = response_mock

        result = tool.process_input("hello")

        chat_mock.process_input.assert_called_once_with("hello")
        response_mock.get_json_serializable.assert_called_once_with()
        self.assertEqual(result, {"msg": "ok"})

    def test_noop_helpers_do_not_raise(self):
        tool, _, _ = self._create_tool_with_mocks()
        tool.load([])
        tool.clear_conversation()


if __name__ == "__main__":
    unittest.main()
