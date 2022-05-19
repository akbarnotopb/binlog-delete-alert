from pymysqlreplication import event, row_event
from dotenv import dotenv_values
import json
from urllib.parse import quote_plus



class Helper:
    def __init__(self):
        self.env = self.getEnv()
        self.user_config = self.getListenerConfig()

    def getEnv(self):
        return dotenv_values(".env")

    def getListenerConfig(self):
        try:
            with open("config/listener.json") as f:
              return json.load(f)
        except FileNotFoundError as e:
            print(e)
        except Exception as e:
            print(e)

    def getMysqlCreds(self):
        return {
                "host": self.env["HOST"] if self.env["HOST"] != "" else "localhost",
                "port": int(self.env["PORT"]) if self.env["PORT"] != "" else 3306,
                "user": self.env["USER"] if self.env["USER"] != "" else "root",
                "passwd": quote_plus(self.env["PASSWORD"]) if self.env["PASSWORD"] != "" else "secret"
            }

    def getConfigs(self):
        # this function will set up the event setting based on listener.json
        config = {}
        evts = { #set all fase
            "deleterows" : (0, row_event.DeleteRowsEvent),
            "writerows" : (0, row_event.WriteRowsEvent),
            "updaterows" : (0, row_event.UpdateRowsEvent),
            "tablemap" : (0, row_event.TableMapEvent),
            "query" : (0, event.QueryEvent),
        }
        if(self.user_config["only_events"] != True and isinstance(self.user_config["only_events"], list)): 
            #if not set true, then manually chose the event
            for evt in self.user_config["only_events"]:
                evts[evt] = (1, evts[evt][1])
        if(self.user_config["ignored_events"] != None and isinstance(self.user_config["ignored_events"], list)): 
            # if not None, then add to ignored event + delete from current only_event config
            config["ignored_events"] = []
            for evt in self.user_config["ignored_events"]:
                evts[evt] = (evts[evt][0] and 0 , evts[evt][1])
                config["ignored_events"].append(evts[evt][1])
        else:
            config["ignored_events"] = None

        #default events
        config["only_events"] = [ row_event.DeleteRowsEvent, row_event.WriteRowsEvent , row_event.UpdateRowsEvent, row_event.TableMapEvent, event.QueryEvent  ]

        #if not default then replace with current only events from evts
        if(self.user_config["only_events"] != True):
            config["only_events"] = [evts[key][1] for key in evts if evts[key][0] == 1 ]
        
        #if not set then set None (default = None = Listen to all)
        config["only_tables"] = self.user_config["only_tables"] if self.user_config["only_tables"] != True and isinstance(self.user_config["only_tables"], list) else None
        config["ignored_tables"] = self.user_config["ignored_tables"] if self.user_config["ignored_tables"] != True and isinstance(self.user_config["ignored_tables"], list) else None
        config["only_schemas"] = self.user_config["only_schemas"] if self.user_config["only_schemas"] != True and isinstance(self.user_config["only_schemas"], list) else None
        config["ignored_schemas"] = self.user_config["ignored_schemas"] if self.user_config["ignored_schemas"] != True and isinstance(self.user_config["ignored_schemas"], list) else None
        return config