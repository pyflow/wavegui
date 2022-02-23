
import string
import random
from datetime import datetime

class IDGenerator(object):
    shift_list = [35, 30, 25, 20, 15, 10, 5, 0]
    charset = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'

    @classmethod
    def format_ts(cls):
        now_ts = int(datetime.now().timestamp())
        id_list = []
        for n in cls.shift_list:
            c = cls.charset[(now_ts >> n) & 31]
            id_list.append(c)
        assert len(id_list) == 8
        return ''.join(id_list)



    @classmethod
    def create_session_id(cls):
        generated = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
        return 'WS{}{}'.format(cls.format_ts(), generated)
    
    @classmethod
    def create_file_id(cls):
        generated = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(20))
        gid = 'UP{}{}'.format(cls.format_ts(), generated)
        return gid.lower()