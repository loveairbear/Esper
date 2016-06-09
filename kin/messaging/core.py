from datetime import datetime



class Conversation:
    """
    An object to track and organize a conversation
    """

    def __init__(self,send_msgs):
        self.transcript = {}
        self.receivedmsgs =[]
        self.sendmsgs = send_msgs
        self.start_time = datetime.now()
        self.last_active = datetime.now()

    def next():
        pass
