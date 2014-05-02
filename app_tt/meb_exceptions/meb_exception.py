# -*- coding: utf-8 -*-

class Meb_exception( Exception ):
    #exception_msgs = {}
    
    def __init__(self):
        #try:
            #if self.exception_msgs.has_key(exc_code):
            self.code = None
            #    self.msg = self.exception_msgs[self.code]
            self.msg = None   
            #else:
            #    raise
        #except Exception:
        #    print "Invalid MEB Exception code"
    
    def __str__(self):
        #return repr(unicode(self.exception_msgs[self.code], "utf-8"))
        return repr(unicode(self.msg, "utf-8"))
    
    #def set_exception_msgs(self, msgs):
    #    self.exception_msgs = msgs
    
    def config_msg(self, *args):
        raise NotImplemented("Should have implemented this")

class Meb_apps_exception( Meb_exception ):
    std_exception_msgs = {
           1 : "MEB-APPS-1: App with empty name",
           2 : "MEB-APPS-2: App with empty shortname",
           3 : "MEB-APPS-3: App with empty description",
           4 : "MEB-APPS-4: Error creating the application",
           5 : "MEB-APPS-5: Error you must supply values into info dict",
           6 : "MEB-APPS-6: Task must be priority between 0 and 1"
          }

    def __init__(self, exc_code):
        #self.set_exception_msgs(self.exception_msgs)
        self.exc_code = exc_code
        self.msg = self.config_msg(exc_code, app_id, app_short_name)
        #super(Meb_apps_exception, self).__init__(exc_code)
    
    def config_msg(self, exc_code, app_id, app_short_name):
        return "%s | app_id : %d | app_short_name: %s" % (self.std_exception_msgs[exc_code], app_id, app_sh_name)
    
class Meb_ttapps_exception( Meb_exception ):
    std_exception_msgs = {
           1 : "MEB-TTAPPS-1: Selection app with empty shortname",
           2 : "MEB-TTAPPS-2: Meta app with empty shortname",
           3 : "MEB-TTAPPS-3: Struct app with empty shortname",
           4 : "MEB-TTAPPS-4: Transcribe app with empty shortname",
           5 : "MEB-TTAPPS-5: Invalid selection app shortname",
           6 : "MEB-TTAPPS-6: Invalid meta app shortname",
           7 : "MEB-TTAPPS-7: Invalid struct app shortname",
           8 : "MEB-TTAPPS-8: Invalid transcribe app shortname"
          }

    def __init__(self, exc_code, app_id, app_sh_name):
        #self.set_exception_msgs(self.exception_msgs)
        self.exc_code = exc_code
        self.msg = self.config_msg(exc_code, app_id, app_sh_name)
        #super(Meb_ttapps_exception, self).__init__(exc_code, msg)
        
    def config_msg(self, app_id, app_sh_name):
        return "%s | app_id : %d | app_short_name: %s" % (self.std_exception_msgs[exc_code], app_id, app_sh_name)

class Meb_pb_task_exception( Meb_exception ):
    std_exception_msgs = {
           1 : "MEB-PB-TASK-1: Cannot find task",
           2 : "MEB-PB-TASK-2: Invalid shortname"
          }
       
    def __init__(self, exc_code, task_id, app_sh_name):
        self.exc_code = exc_code
        self.msg = self.config_msg(exc_code, task_id, app_sh_name)
        #super(Meb_pb_task_exception, self).__init__(exc_code, msg)
    
    def config_msg(self, exc_code, t_id, app_sh_name):
        return "%s | task_id : %d | app_short_name : %s" % (self.std_exception_msgs[exc_code], t_id, app_sh_name)   
        
class Meb_task_factory_exception( Meb_exception ):
    exception_msgs = {
           1 : "MEB-TASK-FACTORY-1: Cannot find app by task"
          }
       
    def __init__(self, exc_code):
        self.set_exception_msgs(self.exception_msgs)
        super(Meb_task_factory_exception, self).__init__(exc_code)