import grpc
from concurrent import futures
import time
import unary_pb2_grpc as pb2_grpc
import unary_pb2 as pb2
import threading

# Associates a unique username with an ip address
accounts_ip = {}

# Associates a username with a logged-in status
accounts_status = {}

# {Matthew: {Nick: [msg1, msg2, msg3], Ryan: [msg1, msg2, msg3]}, Calvin: {John: [msg1, msg2]}, Mike: {} }
accounts_queue = {}

class ChatService(pb2_grpc.ChatServicer):
    def __init__(self, *args, **kwargs):
        pass

    def CreateAccount(self, request, context):
        name = request.name
        if name not in accounts_ip:
            accounts_ip[name] = "localhost"
            accounts_status[name] = False
            accounts_queue[name] = {}
            result = f'I, the server, have added "{name}" to the accounts list.  Size is "{len(accounts_ip)}"'
            response = {'message': result, 'received': True}
        else:
            result = "Error: Username already in use"
            response = {'message': result, 'received': True}
        
        return pb2.ServerResponse(**response)

    # Once use logs in, server immediately creates a thread for that user that is working on user's behalf
    # Looking for messages
    def Login(self, request, context):
        name = request.name
        if name in accounts_ip:
            # should be able to login from multiple different hosts
            # so not checking if already logged in
            
            accounts_status[name] = True
            result = f'You, "{name}", are logged in'
            response = {'message': result, 'received': True}
        else:
            result = "Error: Not a registered account.  Create an account"
            response = {'message': result, 'received': True}

        return pb2.ServerResponse(**response)

    def ListAccounts(self, request, context):
        accounts_str = ""
        for account in accounts_ip:
            accounts_str += account + " "
        response = {'accounts': accounts_str}
        return pb2.Accounts(**response)

    # Send Message puts message into the destination user's queue
    def SendMessage(self, request, context):
        destination = request.destination
        source = request.source
        text = request.text

        #Todo: maybe check source is in accounts          
        #if accounts_status[source] == False:
        #    result = "Error: You are not logged in"
        #elif destination not in accounts_ip:
        #    result = "Error: Sending to an invalid user"
        # Whether or not destination is logged in, put it in queue
        #else:
        if source not in accounts_queue[destination]:
            accounts_queue[destination][source] = [text]
        else:
            accounts_queue[destination][source].append(text)
        result = "Message Sent"
        response = {'message': result, 'received': True}
        return pb2.ServerResponse(**response)

    def ListenMessages(self, request, context):
        name = request.name
        while True:
            myDict = accounts_queue[name]
            for sender in myDict:
                for msg in myDict[sender]:
                    response = {'destination': name, 'source': sender, 'text': msg}
                    yield pb2.MessageInfo(**response)
                    myDict[sender].remove(msg)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pb2_grpc.add_ChatServicer_to_server(ChatService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()