from pymysqlreplication import BinLogStreamReader
from pymysqlreplication import event, row_event
import cryptography #required for mysql8.0, tested on docker version 
from dotenv import dotenv_values
import json
from urllib.parse import quote_plus
import smtplib
from datetime import datetime

ENV = dotenv_values(".env")
with open("listener.json") as f:
    USER_CONFIG = json.load(f)

MYSQL_SETTINGS = {
    "host": ENV["HOST"] if ENV["HOST"] != "" else "localhost",
    "port": int(ENV["PORT"]) if ENV["PORT"] != "" else 3306,
    "user": ENV["USER"] if ENV["USER"] != "" else "root",
    "passwd": quote_plus(ENV["PASSWORD"]) if ENV["PASSWORD"] != "" else "secret"
}

def getConfigs():
    # this function will set up the event setting based on listener.json
    config = {}
    evts = { #set all fase
        "deleterows" : (0, row_event.DeleteRowsEvent),
        "writerows" : (0, row_event.WriteRowsEvent),
        "updaterows" : (0, row_event.UpdateRowsEvent),
        "tablemap" : (0, row_event.TableMapEvent),
        "query" : (0, event.QueryEvent),
    }
    if(USER_CONFIG["only_events"] != True and isinstance(USER_CONFIG["only_events"], list)): 
        #if not set true, then manually chose the event
        for evt in USER_CONFIG["only_events"]:
            evts[evt] = (1, evts[evt][1])
    if(USER_CONFIG["ignored_events"] != None and isinstance(USER_CONFIG["ignored_events"], list)): 
        # if not None, then add to ignored event + delete from current only_event config
        config["ignored_events"] = []
        for evt in USER_CONFIG["ignored_events"]:
            evts[evt] = (evts[evt][0] and 0 , evts[evt][1])
            config["ignored_events"].append(evts[evt][1])
    else:
        config["ignored_events"] = None

    #default events
    config["only_events"] = [ row_event.DeleteRowsEvent, row_event.WriteRowsEvent , row_event.UpdateRowsEvent, row_event.TableMapEvent, event.QueryEvent  ]

    #if not default then replace with current only events from evts
    if(USER_CONFIG["only_events"] != True):
        config["only_events"] = [evts[key][1] for key in evts if evts[key][0] == 1 ]
    
    #if not set then set None (default = None = Listen to all)
    config["only_tables"] = USER_CONFIG["only_tables"] if USER_CONFIG["only_tables"] != True and isinstance(USER_CONFIG["only_tables"], list) else None
    config["ignored_tables"] = USER_CONFIG["ignored_tables"] if USER_CONFIG["ignored_tables"] != True and isinstance(USER_CONFIG["ignored_tables"], list) else None
    config["only_schemas"] = USER_CONFIG["only_schemas"] if USER_CONFIG["only_schemas"] != True and isinstance(USER_CONFIG["only_schemas"], list) else None
    config["ignored_schemas"] = USER_CONFIG["ignored_schemas"] if USER_CONFIG["ignored_schemas"] != True and isinstance(USER_CONFIG["ignored_schemas"], list) else None
    return config

def sendMail(message, eventype, table):
    # this function will send the email
    fromaddr = ENV["EMAIL"]
    message = "From: {fromaddr} \n"\
                "To: {to} \n"\
                "Cc: {cc} \n"\
                "Bcc: {bcc} \n"\
                "MIME-Version: 1.0 \n"\
                "Content-type: text/html \n"\
                "Subject:{subject} \n\n"\
                "{message}".format(fromaddr=fromaddr, to=",".join(USER_CONFIG["recipient"]), cc = ",".join(USER_CONFIG["cc"]), bcc = ",".join(USER_CONFIG["bcc"]), subject= "{} detected at {}".format(eventype, table), message= message )

    toaddrs = USER_CONFIG["recipient"] + USER_CONFIG["cc"] + USER_CONFIG["bcc"]
    with smtplib.SMTP(host = ENV["EMAIL_HOST"], port= int(ENV["EMAIL_PORT"]) ) as server:
        if(ENV["EMAIL_AUTH"] == "True"):
            server.login(ENV["EMAIL"], ENV["EMAIL_PASSWORD"])
        # server.set_debuglevel(1)
        server.sendmail(fromaddr, toaddrs, message)


def main():
    # server_id is your slave identifier, it should be unique.
    # set blocking to True if you want to block and wait for the next event at
    # the end of the stream
    conf = getConfigs()
    stream = BinLogStreamReader(connection_settings=MYSQL_SETTINGS,
                                server_id=1,
                                blocking=True, 
                                only_schemas=conf["only_schemas"],
                                ignored_schemas=["ignored_schemas"],
                                only_events=conf["only_events"], 
                                ignored_events=conf["ignored_events"], 
                                only_tables=conf["only_tables"], 
                                ignored_tables=conf["ignored_events"])

    for binlogevent in stream:
        event_type = binlogevent.event_type

        if(event_type == 32): #only delete for notification
            event_type = "DeleteRows"
            schema = binlogevent.__dict__["schema"]+"."+binlogevent.__dict__["table"]
            at = datetime.fromtimestamp(binlogevent.__dict__["timestamp"])
            rows = json.dumps(binlogevent.rows)

            message = "At : {at}  <br>"\
                    "Event Type : {event} <br>"\
                    "Schema.Table : {schema}  <br>"\
                    "Data : {data}".format(at = str(at.strftime("%m/%d/%Y %H:%M:%S")) , data = str(rows), event = event_type, schema = schema )
            if(len(USER_CONFIG["recipient"]) > 0): #if recipient  more than 1
                sendMail(message, eventype=str(event_type), table=str(schema))
        
        binlogevent.dump()




# if __name__ == "__main__":
#     main()