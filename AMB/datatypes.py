from datetime import datetime


class Appointment:
    def __init__(self, appointment_id=None, user_id: int = None, admin_id: int = None, time_ordered: datetime = None, order_number: int = None, is_done: bool = False, is_cancelled: bool = False, cancelled_by: int = None):
        self.appointment_id=appointment_id
        self.user_id=user_id
        self.admin_id=admin_id
        self.time_ordered=time_ordered
        self.order_number=order_number
        self.is_done=is_done
        self.is_cancelled=is_cancelled
        self.cancelled_by=cancelled_by
        
class User:
    def __init__(self,user_id:int=None,is_admin:bool=None,user_name:str=None,mention:str=None,recieve_weekly=True,get_all=False,language="en"):
        self.user_id=user_id
        self.is_admin=is_admin
        self.user_name=user_name
        self.mention=mention
        self.recieve_weekly=recieve_weekly
        self.get_all=get_all
        self.language=language

        
        