from unittest import mock, TestCase, main
from esper.messaging import fb_msgr as fb

# -*- coding: utf-8 -*-

def mod_recurse(*args,**kwargs):
    arguments = kwargs.get('args')
    return fb.recurse(*arguments)


class FbMsgrTests(TestCase):

    @mock.patch('esper.messaging.fb_msgr.recurse.apply_async')
    @mock.patch('esper.messaging.fb_msgr.db.FbUserInfo.objects')
    def test_recurse(self, test_userdata, test_async_recurse):
        """
        Test for _ things:
            Recurse is called the full length of iterator and is ETAd
            a day apart

            Send_msgs is called through all events before the next recurse

        """
        test_async_recurse.side_effect = mod_recurse
        test_userdata = {
                        "fb_id": "1230230285720",
                        "account": "23078230",
                        "timezone": "UTC",
                        "gender": "male",
                        "name": "John Doe",
                        "optout": True,
                        "activated": True
                        }

        with mock.patch('esper.messaging.fb_msgr.send_msgs.apply_async') as mockmsgs:
            fb_obj = iter(range(1, 10))
            fb.recurse(fb_obj, test_userdata)
            print(test_async_recurse.call_args_list)
            calls = mockmsgs.call_args_list.encode('utf8')
            print(calls)




if __name__ == '__main__':
    main()