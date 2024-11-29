import time

class Message:
    def __init__(self, text: str, object: object = None):
        self.timeStamp = time.time()
        self.text = text
        self.object = object

class MessageBus:

    def __init__(self):
        self.messages = dict[float, Message]()

    #SINGLETON MANAGEMENT
    _bus_instance = None

    @staticmethod
    def getSingletonInstance():
        #global _bus_instance
        if MessageBus._bus_instance is None:
            MessageBus._bus_instance = MessageBus()
        return MessageBus._bus_instance 

    #BUS EXTERNAL INTERRACTIONS
    @staticmethod
    def emitMessage(messageText: str, enclosedObject : object = None) -> None:
        newMessage = Message(messageText, enclosedObject)
        messageBus = MessageBus.getSingletonInstance()
        messageBus.messages[newMessage.timeStamp] = newMessage

    @staticmethod
    def readMessages(beginTimeStamp: float = None, endTimeStamp: float = None) -> list[Message]:
        messageBus = MessageBus.getSingletonInstance()
        returnedMessages = list[Message]()
        for timeStamp in messageBus.messages.keys():
            if beginTimeStamp is None or beginTimeStamp <= timeStamp:
                if endTimeStamp is None or endTimeStamp >= timeStamp:
                    returnedMessages.append(messageBus.messages[timeStamp])

        return returnedMessages
    
    @staticmethod
    def getCurrentTimeStamp():
        return time.time()
