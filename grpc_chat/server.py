import grpc
from concurrent import futures
import time
import unary_pb2_grpc as pb2_grpc
import unary_pb2 as pb2
import threading

# Associates a unique username with a password
accounts = {}

# Associates a username with a logged-in status
accounts_status = {}

# {Matthew: {Nick: [msg1, msg2, msg3], Ryan: [msg1, msg2, msg3]}, Calvin: {John: [msg1, msg2]}, Mike: {} }
accounts_queue = {}

class ChatService(pb2_grpc.ChatServicer):
    def __init__(self, *args, **kwargs):
        pass

    def CreateAccount(self, request, context):
        username = request.username
        password = request.password
        if username not in accounts:
            accounts[username] = password
            accounts_status[username] = False
            accounts_queue[username] = {}
            result = f'"{username}" added'
            response = {'message': result, 'error': False}
        else:
            result = "Error: Username already in use"
            response = {'message': result, 'error': True}
        
        return pb2.ServerResponse(**response)

    # Once use logs in, server immediately creates a thread for that user that is working on user's behalf
    # Looking for messages
    def Login(self, request, context):
        username = request.username
        password = request.password
        
        if username not in accounts:
            result = f'"{username}" is not a registered account.'
            response = {'message': result, 'error': True}
            return pb2.ServerResponse(**response)

        if password != accounts[username]:
            result = "Password does not match username"
            response = {'message': result, 'error': True}
            return pb2.ServerResponse(**response)
            
        accounts_status[username] = True
        result = f'"{username}", you are logged in'
        response = {'message': result, 'error': False}
        return pb2.ServerResponse(**response)

    def Logout(self, request, context):
        username = request.username
        accounts_status[username] = False
        result = f'"{username}", you are logged out'
        response = {'message': result, 'error': False}
        return pb2.ServerResponse(**response)

    def ListAccounts(self, request, context):
        accounts_str = ""
        for account in accounts:
            accounts_str += account + " "
        response = {'usernames': accounts_str}
        return pb2.Accounts(**response)

    # Send Message puts message into the destination user's queue
    def SendMessage(self, request, context):
        destination = request.destination
        source = request.source
        text = request.text

        if source not in accounts or accounts_status[source] == False:
            result = "Error: username not valid or not logged in"
            response = {'message': result, 'error': True}
            return pb2.ServerResponse(**response)

        if destination not in accounts:
            result = "Error: destination not valid"
            response = {'message': result, 'error': True}
            return pb2.ServerResponse(**response)
            
        if source not in accounts_queue[destination]:
            accounts_queue[destination][source] = [text]
        else:
            accounts_queue[destination][source].append(text)
        result = "Message Sent"
        response = {'message': result, 'error': False}
        return pb2.ServerResponse(**response)

    def ListenMessages(self, request, context):
        username = request.username
        while True:
            myDict = accounts_queue[username]
            for sender in myDict:
                for msg in myDict[sender]:
                    response = {'destination': username, 'source': sender, 'text': msg}
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