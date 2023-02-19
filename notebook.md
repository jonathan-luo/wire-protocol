# Engineering Notebook #

## Connecting to the Server ##
When the user runs the client program, they will be prompted to enter the IP address of the server, which they can then connect to.

We got the computers to communicate by finding the IP address of the server under Mac > Settings > Wifi. One solution was to hardcode this address into the client.py file of the client computer. However, we ended up doing something more dynamic, by allowing users to specify the server IP address that they would connect to as a command-line prompt.

## Logging In/Creating an Account ##
Once logged in and connected to the server, the user will be prompted to enter their username.
If the username exists in the system, then they must enter their password. They have up to 3 tries to enter the correct password. They also have the option to quit, which would then alert the server to close this client. If they correctly get the password, then they are logged in.
If the username doesn’t exist in the system, then they must create a new password and then enter a confirmation password to make a new account. Whenever they enter the wrong confirmation password, they have the option to quit or retry a different password.

- Onboarding

    The server sees: `0 [args]`

## Selection Screen ##
Once successfully logged in, the user will be greeted with a welcome message, as well as the notification of how many of the same account are logged into the system. They will receive all the undelivered messages. Then, they will receive a selection screen for what they want to do next. The menu consists of:

- List All Accounts

    The server sees: `1 [arg : str]`

- Send A Message

    The server sees: `2 [username] [message]`

- Delete Account

    The server sees: `8`

- Quit

    The server sees: `9`