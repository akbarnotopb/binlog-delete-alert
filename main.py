from pymysqlreplication import BinLogStreamReader
import cryptography #required for mysql8.0, tested on docker MySQL 8.0 
import json
from datetime import datetime
from helper import Helper
from mailer import MailDebounce

helper = Helper()
mailer = MailDebounce()
ENV = helper.getEnv()
USER_CONFIG = helper.getListenerConfig()
MYSQL_SETTINGS = helper.getMysqlCreds()

def updateLastRun(timestamp):
    with open("config/lastdelete.timestamp", "w") as f:
        f.write(str(timestamp))

def getLastRun():
    try:
        with open("config/lastdelete.timestamp", "r") as f:
            data = f.read()
        return int(data) if data != "" else None
    except FileNotFoundError as e:
        return None

def main(start_at = None):
    # server_id is your slave identifier, it should be unique.
    # set blocking to True if you want to block and wait for the next event at
    # the end of the stream
    print(start_at)
    conf = helper.getConfigs()
    print(conf)
    stream = BinLogStreamReader(connection_settings=MYSQL_SETTINGS,
                                server_id=1,
                                blocking=True, 
                                freeze_schema=False,
                                only_schemas=conf["only_schemas"],
                                ignored_schemas=["ignored_schemas"],
                                only_events=conf["only_events"], 
                                ignored_events=conf["ignored_events"], 
                                only_tables=conf["only_tables"], 
                                ignored_tables=conf["ignored_events"])
    for binlogevent in stream:
        event_type = binlogevent.event_type

        if(event_type == 32): #only delete for notification
            print("hard delete detected")
            event_type = "DeleteRows"
            schema = binlogevent.__dict__["schema"]+"."+binlogevent.__dict__["table"]
            at = datetime.fromtimestamp(binlogevent.__dict__["timestamp"])
            rows = json.dumps(binlogevent.rows)

            message = "At : {at}  <br>"\
                    "Event Type : {event} <br>"\
                    "Schema.Table : {schema}  <br>"\
                    "Data : {data}".format(at = str(at.strftime("%m/%d/%Y %H:%M:%S")) , data = str(rows), event = event_type, schema = schema )
            if(USER_CONFIG["save_last_delete"]):
                updateLastRun(binlogevent.timestamp)
            if(len(USER_CONFIG["recipient"]) > 0): #if recipient  more than 1
                mailer.debounceMail(message)
        
        binlogevent.dump()


if __name__ == "__main__":    
    if(USER_CONFIG["save_last_delete"]):
        main(start_at = getLastRun())
    else:
        main(start_at = None)