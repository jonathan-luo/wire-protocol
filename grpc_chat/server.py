import grpc
from concurrent import futures
import time
import unary_pb2_grpc as pb2_grpc
import unary_pb2 as pb2

# Associates a unique username with an ip address
accounts = {}

# Associates a username with a logged-in status
accounts_status = {}

# Associates a username with a message queue
accounts_queue = {}

class ChatService(pb2_grpc.ChatServicer):
    def __init__(self, *args, **kwargs):
        pass

    def CreateAccount(self, request, context):
        name = request.name
        if name not in accounts:
            accounts[name] = "localhost"
            accounts_status[name] = False
            result = f'I, the server, have added "{name}" to the accounts list.  Size is "{len(accounts)}"'
            response = {'message': result, 'received': True}
        else:
            result = "Error: Username already in use"
            response = {'message': result, 'received': True}
        
        return pb2.ServerResponse(**response)

    def Login(self, request, context):
        name = request.name
        if name in accounts:
            # should be able to login from multiple different hosts
            # so not checking if already logged in
            
            #ToDo: update ip address, or add it to a list of ip addresses
            accounts_status[name] = True
            result = f'You, "{name}", are logged in'
            response = {'message': result, 'received': True}
        else:
            result = "Error: Not a registered account.  Create an account"
            response = {'message': result, 'received': True}

        return pb2.ServerResponse(**response)

    def ListAccounts(self, request, context):
        accounts_str = ""
        for account in accounts:
            accounts_str += account + " "
        response = {'accounts': accounts_str}
        return pb2.Accounts(**response)

    def SendMessage(self, request, context):
        destination = request.destination
        source = request.source
        text = request.text
        #Todo: maybe check source is in accounts          
        if accounts_status[source] == False:
            result = "Error: You are not logged in"
        elif destination not in accounts:
            result = "Error: Sending to an invalid user"
        # Whether or not destination is logged in, put it in queue
        else:
            accounts_queue[destination].append(text)
            result = "Message Sent"

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pb2_grpc.add_ChatServicer_to_server(ChatService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()