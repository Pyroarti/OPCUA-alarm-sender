import unittest
from unittest.mock import patch, MagicMock
import asyncio
from opcua_alarm import SubHandler

class TestUserNotification(unittest.TestCase):

    def setUp(self):
        self.subhandler_instance = SubHandler("1.1.1.1:1111")

    @patch('opcua_alarm.sms_queue.put')
    @patch('opcua_alarm.logger_opcua_alarm')
    def test_user_notification(self, mock_logger, mock_sms_queue_put):
        mock_sms_queue_put.return_value = None

        test_cases = [
            {"message": "Test Alarm 1", "severity": 5, "expected_send": True},
        ]

        for case in test_cases:
            asyncio.run(self.subhandler_instance.user_notification(case["message"], case["severity"]))

            if case["expected_send"]:
                mock_sms_queue_put.assert_called()
                mock_logger.assert_called_with(f"Sent SMS to [user name]")
            else:
                mock_sms_queue_put.assert_not_called()

            mock_sms_queue_put.reset_mock()

if __name__ == '__main__':
    unittest.main()
