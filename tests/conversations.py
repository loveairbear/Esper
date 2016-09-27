import unittest as utest
from unittest import mock
from esper.messaging import core_msgr as core
from datetime import datetime
class FbMsgrTests(utest.TestCase):
    init_msg = {
            "sender": {
                "id": "USER_ID"
            },
            "recipient": {
                "id": "PAGE_ID"
            },
            "timestamp": 1474143570359,
            "message": {
                "mid": "mid.1457764197618:41d102a3e1ae206a38",
                "seq": 73,
                "text": "hello, world!",
                "quick_reply": {
                    "payload": "DEVELOPER_DEFINED_PAYLOAD"
                }
            }
        }
    def test_list_instances(self):
        instances = []
        core.Conversation._instances = []
        for i in range(10):
            instances.append(core.Conversation(self.init_msg, i, None))
        count = 0
        for inst in core.Conversation.list_instances():
            self.assertTrue(inst is instances[count])
            count += 1

    def test_remove_instance(self):

        convo1 = core.Conversation(self.init_msg, 400, None)
        self.init_msg['timestamp'] = core.datetime.utcnow().timestamp() * 1000
        convo2 = core.Conversation(self.init_msg, 600, None)
        core.Conversation.decayed_instances()
        self.assertEqual(len(core.Conversation.list_instances()), 1)

    def test_find_instance(self):
        convo = core.Conversation(self.init_msg, 456, None)
        print(core.Conversation.get_instance(456))
        print(convo)
        self.assertEqual(core.Conversation.get_instance(456), convo)

if __name__ == '__main__':
    utest.main()