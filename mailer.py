import smtplib
from threading import Timer
from helper import Helper


DEBOUNCE_TIME = 10  # 1 second


class MailDebounce:

    def __init__(self):
        helper = Helper()
        self.__message = []
        self.__debounced_messaged = []
        self.__user_config = helper.getListenerConfig()
        self.__env = helper.getEnv()
        self.__debounce_action = None

    def debounceMail(self, message):
        if self.__debounce_action:  
            self.__debounce_action.cancel() #if debounced -> cancel ongoing email thread send
            self.__message = self.__debounced_messaged + self.__message # rollback the debounced message
            print("mail debounced")
        
        def sendMail(message, fromaddr, toaddrs, env, auth = True):
            with smtplib.SMTP(host = env["EMAIL_HOST"], port= int(env["EMAIL_PORT"]) ) as server:
                if(auth):
                    server.login(env["EMAIL"], env["EMAIL_PASSWORD"])
                # server.set_debuglevel(1)
                server.sendmail(fromaddr, toaddrs, message)
        
        self.__message.append(message)
        message = "<br><br><br>".join(self.__message)
        fromaddr = self.__env["EMAIL"]
        message = "From: {fromaddr} \n"\
            "To: {to} \n"\
            "Cc: {cc} \n"\
            "Bcc: {bcc} \n"\
            "MIME-Version: 1.0 \n"\
            "Content-type: text/html \n"\
            "Subject:{subject} \n\n"\
            "{message}".format(fromaddr=fromaddr, to=",".join(self.__user_config["recipient"]), cc = ",".join(self.__user_config["cc"]), bcc = ",".join(self.__user_config["bcc"]), subject= "{} delete event detected!".format(len(self.__message)), message= message )
        toaddrs = self.__user_config["recipient"] + self.__user_config["cc"] + self.__user_config["bcc"]

        self.__debounced_messaged = self.__message
        self.__message = []
        self.__debounce_action = Timer(DEBOUNCE_TIME, sendMail, args=[message, fromaddr, toaddrs, self.__env, True if self.__env["EMAIL_AUTH"] == "True" else False])
        self.__debounce_action.start()