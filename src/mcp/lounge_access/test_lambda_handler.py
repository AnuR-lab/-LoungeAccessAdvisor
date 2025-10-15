import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch, MagicMock
import os
import sys

# Ensure the tests can import modules from this package directory
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)

from lambda_handler import lambda_handler


def make_context(tool_name=None):
    """Create a lightweight mock Lambda context with optional tool name."""
    client_context = None
    if tool_name is not None:
        client_context = SimpleNamespace(custom={"bedrockAgentCoreToolName": tool_name})
    return SimpleNamespace(client_context=client_context)


class TestLambdaHandler(unittest.TestCase):
    @patch("lambda_handler.LoungeAccessClient")
    @patch("lambda_handler.tool_example_1")
    def test_tool_example_1_success_with_delimiter(self, mock_tool1, mock_client_cls):
        # Arrange
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_tool1.return_value = [{"name": "n1", "id": "1"}]
        # Tool comes via client_context with a prefix and delimiter
        ctx = make_context("prefix___tool_example_1")

        # Act
        resp = lambda_handler(event={}, context=ctx)

        # Assert
        self.assertEqual(resp["statusCode"], 200)
        body = json.loads(resp["body"])
        self.assertEqual(body["result"], [{"name": "n1", "id": "1"}])
        mock_client_cls.assert_called_once_with()
        mock_tool1.assert_called_once_with(mock_client)

    @patch("lambda_handler.LoungeAccessClient")
    @patch("lambda_handler.tool_example_1")
    def test_tool_example_1_success_without_delimiter(self, mock_tool1, mock_client_cls):
        # Arrange
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_tool1.return_value = [{"name": "n1", "id": "1"}]
        # Tool name provided exactly
        ctx = make_context("tool_example_1")

        # Act
        resp = lambda_handler(event={}, context=ctx)

        # Assert
        self.assertEqual(resp["statusCode"], 200)
        body = json.loads(resp["body"])
        self.assertEqual(body["result"], [{"name": "n1", "id": "1"}])
        mock_client_cls.assert_called_once_with()
        mock_tool1.assert_called_once_with(mock_client)

    @patch("lambda_handler.LoungeAccessClient")
    @patch("lambda_handler.tool_example_2")
    def test_tool_example_2_missing_parameters(self, mock_tool2, mock_client_cls):
        # Arrange
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        ctx = make_context("tool_example_2")
        event = {}  # no parameter_1 or parameter_2

        # Act
        resp = lambda_handler(event=event, context=ctx)

        # Assert
        self.assertEqual(resp["statusCode"], 400)
        body = json.loads(resp["body"])
        self.assertIn("error", body)
        self.assertEqual(body["error"], "Missing input parameters")
        mock_tool2.assert_not_called()

    @patch("lambda_handler.LoungeAccessClient")
    @patch("lambda_handler.tool_example_2")
    def test_tool_example_2_success(self, mock_tool2, mock_client_cls):
        # Arrange
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_tool2.return_value = {"ok": True}
        ctx = make_context("prefix___tool_example_2")
        event = {"parameter_1": "a", "parameter_2": "b"}

        # Act
        resp = lambda_handler(event=event, context=ctx)

        # Assert
        self.assertEqual(resp["statusCode"], 200)
        body = json.loads(resp["body"])
        self.assertEqual(body["result"], {"ok": True})
        mock_tool2.assert_called_once_with("a", "b", mock_client)

    @patch("lambda_handler.LoungeAccessClient")
    @patch("lambda_handler.tool_example_2")
    def test_tool_example_2_value_error(self, mock_tool2, mock_client_cls):
        # Arrange
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_tool2.side_effect = ValueError("Bad params")
        ctx = make_context("tool_example_2")
        event = {"parameter_1": "a", "parameter_2": "b"}

        # Act
        resp = lambda_handler(event=event, context=ctx)

        # Assert
        self.assertEqual(resp["statusCode"], 400)
        body = json.loads(resp["body"])
        self.assertEqual(body["error"], "Bad params")
        mock_tool2.assert_called_once_with("a", "b", mock_client)

    def test_unknown_tool_when_no_context(self):
        # Arrange: context without client_context yields unknown tool
        ctx = SimpleNamespace(client_context=None)

        # Act
        resp = lambda_handler(event={}, context=ctx)

        # Assert
        self.assertEqual(resp["statusCode"], 400)
        body = json.loads(resp["body"])
        self.assertEqual(body["error"], "Unknown tool")


if __name__ == "__main__":
    unittest.main()
