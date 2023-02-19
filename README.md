# Wire Protocol: Chat Application ###
## Description
This is a simple chat client/server application with the following functions:
- Create an account: You must supply a unique user name and remember your password.
- List accounts (or a subset of the accounts, by text wildcard).
- Send a message to a recipient: If the recipient is logged in, deliver immediately; otherwise queue the message and deliver on demand.
- Deliver undelivered messages to a particular user.
- Delete an account.

Created by Michael Hu, Jonathan Luo and Matt Kiley.
## Usage
### Requirements
To make sure you have all the required modules for this application, run `pip install -r requirements.txt` before continuing!
### Server
To get started, one machine needs to start the server by running `python server.py` once they are in this directory. They must make sure this server remains active for clients to connect.
### Client
Then, other machines can connect to the server by running `python client.py`. The client server will prompt the user to enter the IP address of the server machine. To find the IP address of a Mac, go to <span style="color:#528AAE">System Settings > Wi-Fi > [Your Network] > Details > TCP/IP</span>. To find the IP address of a Windows machine, go to <span style="color:#528AAE">Start > Settings > Network & Internet > Wi-Fi > Properties > IPv4 </span>. Once the client is successfully connected to the server, our application is now up and running--enjoy chatting!