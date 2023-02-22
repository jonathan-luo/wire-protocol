# Engineering Notebook #

## Connecting to the Server ##
When the user runs the client program, they will be prompted to enter the IP address of the server, which they can then connect to.

We got the computers to communicate by finding the IP address of the server under Mac > Settings > Wifi. One solution was to hardcode this address into the client.py file of the client computer. However, we ended up doing something more dynamic, by allowing users to specify the server IP address that they would connect to as a command-line prompt.

## Command Format ##

The communication between the client and server is done by sending commands in a specific format. Each command is represented as a string with a unique identifier at the beginning, followed by zero or more arguments separated by pipes, which look like `|`. The identifier is an integer and serves to distinguish the different types of commands that can be sent, and the arguments may differ depending on the type of commands. To protect against injection attacks, we ban users from putting pipes into their messages and login details.

## Logging In/Creating an Account ##
Once logged in and connected to the server, the user will be prompted to enter their username.
If the username exists in the system, then they must enter their password. They have up to 3 tries to enter the correct password. They also have the option to quit, which would then alert the server to close this client. If they correctly enter their password, then they are logged in.
If the username doesn’t exist in the system, then they must create a new password and then enter a confirmation password to make a new account. Whenever they enter the wrong confirmation password, they have the option to quit or retry a different password.

- Onboarding

    The part of the process is separate from the rest of the commands since it's required before the user can make any choices.

    The server sees: `LOGIN_COMMAND [username : str]`

    When the client and the server sends this command in the above format, the two can assert that the conversation is about the login process still. The client will first send an username over, and the server will check if the username already exists in the accounts dictionary. If it does, the server will ask for the user's password and check it against the stored hash. If it doesn't, the server will create a new account for the user.

- Login Existing User

    The client sees: `LOGIN_COMMAND exists`

    If the username exists in the accounts dictionary, the server will send this message to the client, prompting the user to enter their password.

    The server sees: `LOGIN_COMMAND [password : str]`
    The client sees: `LOGIN_COMMAND success` or `LOGIN_COMMAND error`

    The server then repeatedly checks if the password entered by the user matches the stored password hash, giving them up to three chances to enter it correctly. If the user fails to enter the correct password within three tries, or if the user quits, the server will end the connection.

    If the user enters the correct password, the server will log the user in by adding the client to the `connected_clients` dictionary under the username of the user and send a success message to the client. The server will then print a message indicating that the user has joined the chat.

- Create New Account

    The client sees: `LOGIN_COMMAND new`

    If the username does not exist in the `accounts` dictionary, the server will create a new lock associated with the username and add it to the `user_locks` dictionary.

    The server will then send a message to the client, prompting the user to create a new password.

    The server sees: `LOGIN_COMMAND [new_password : str]`
    The client sees: `LOGIN_COMMAND success`

    After the user enters the new password, the client will ask for confirmation of the password. If the confirmation password does not match the new password, the client will ask if the user wants to quit or retry again.

    If the confirmation password matches the new password, the server will hash the password and add it to the `accounts` dictionary, then log the user in by adding the client to the `connected_clients` dictionary and send a success message to the client. The server will then print a message indicating that the user has joined the chat.

## Selection Screen ##
Once successfully logged in, the user will be greeted with a welcome message, as well as the notification of how many of the same account are logged into the system. They will receive all the undelivered messages.

Behind the scenes, we've created a thread on the server end for communicating with this specific client and two threads on the client end to handle user input and message reception. The client's `user_thread` takes care of the main client-to-server interactions such as the login process and the selection screen. The `message_reception_thread` will be listening for new undelivered message, and if any of it starts with `RECEIVE_MESSAGE_COMMAND`, then we display the message to the user immediately. Otherwise, they go in the `server_message_queue` to be processed later.

- Receive Messages

    The client sees: `RECEIVE_MESSAGE_COMMAND [sender : str] [recipient : str] [message : str] [time : str] [padding : ' ']`

    The server sends messages to the client using the `RECEIVE_MESSAGE_COMMAND` command. When the client receives a message, it is displayed in the client's UI using the `display_message()` function. The string packs four elements of the message: the sender of the message, the recipient of the message, the message text, and the time the message was sent, which can all be extracted from the string by first removing the padding spaces and extra pipe from the end and then use the rest of the pipes as delimiters (like for any other message from the server). The padding spaces are used to ensure that multiple messages in a client's inbox are delivered smoothly. These variables are then passed to the `display_message()` function, which is responsible for displaying the message on the client's terminal immediately.

The user's selection menu consists of:

- List All Accounts

    The server sees: `VIEW_USERS_COMMAND [arg : str = '*']`

    The method by which users can specify their search criteria is as follows: Once they select "View Users" as their desired task, a prompt pops up asking if they would like to submit a wildcard query for specific users. Leaving this prompt blank (i.e., by simply pressing Enter) will return all active users other than the current user, if any. Otherwise, the user can specify, using GLOB wildcard syntax, usernames that they wish to query for. On the backend, searching is done by converting the GLOB query into Regex using the `fnmatch.translate` function. Then, that regex pattern is compiled and used to filter over all active users (other than the current user). If no matches are found, "No users found." is printed, which is the same behavior as when there are no other active users at all.

- Send A Message

    The server sees: `SEND_MESSAGE_COMMAND [username : str] [message : str]`

    When the user logs in, any undelivered messages that were sent to them while they were offline are sent to them. When the user selects "Send A Message," they are prompted to enter the username of the recipient and the message they want to send. If the recipient is currently logged in, the message is immediately delivered to all of their connected devices. Otherwise, the message is added to a queue for the recipient and will be delivered the next time they log in. A success message is sent back to the client once the message is sent.

    When a message is sent from one user to another, it is either immediately delivered to the recipient's connected clients, or it is added to a queue to be delivered the next time the recipient logs in. If the recipient is currently logged in, the `deliver_new_message()` function is called to deliver the message to all of their connected devices. If the recipient is not logged in, the message is added to a queue for the recipient in the `unsent_message_queue` dictionary. Once the recipient logs in, all of their undelivered messages are immediately sent to them, including messages that were in the queue. The message is also stored in the message history `messages` dictionary on the server.


- Delete Account

    The server sees: `DELETE_ACCOUNT_COMMAND [username : str]`

    When a user chooses to delete their account, a number of steps occur. Namely, first, if the user is logged in on multiple devices, the client making the deletion request is notified of this (this is done by sending the Verify Account Only Logged In On One Device hidden operation, detailed below), and is prompted whether they would like to log out of each of the other devices or not. If not, the account deletion workflow terminates. Otherwise, the Log Out All Other Instances hidden operation, documented below, is utilized to log out the user from each of the devices that was NOT the initiating client*.

    After this succeeds, the user is then prompted to enter their password to complete deletion. If this password is correct (i.e., its SHA256 hash matches the password hash stored for the account), then account deletion completes (`delete_account()` is called), deleting the account's information from the `accounts` and `unsent_message_queue` dictionaries (more details in Locks section below). If the password is incorrect, the account deletion workflow is terminated, and a message is printed, stating "Your password was incorrect, account deletion cancelled."

    *Note: Due to the nature of `inquirer` prompts, although the other clients are terminated (i.e., their sockets are closed, and their information is removed from the `connected_clients` dictionary), these other clients cannot be immediately terminated in the terminal, since the `inquirer` prompt is still pending. To fully terminate these clients, simply pressing ctrl+c as a keyboard interrupt suffices, or toggling to select Quit/Log Out as one of the `inquirer` options. Also because of this behavior, the `while True:` loop within the `handle_client()` function in `client.py` is wrapped in a try-except block, to suppress the error messages that arise from using ctrl+c or initiating calls through a closed socket.

- Quit

    The server sees: `QUIT_COMMAND`

In addition to these selectable operations for users, there also exist hidden operations such as the following, which are also part of our wire protocol definition, but not explicitly available for the user to invoke. These are often part of validating user input, such as ensuring that users send messages only to registered users, or that they can only delete an account when it is only logged into one device.

- Verify Registered User

    The server sees: `CHECK_ACCOUNT_COMMAND [username : str]`

    The server checks if the username exists and sends a message back to the client indicating whether or not the account exists.

- Verify Account Only Logged In On One Device

    The server sees: `MULTIPLE_LOGIN_COMMAND`

    The server checks if the user has logged in from multiple devices and sends a message back to the client indicating whether or not multiple logins exist.

- Log Out All Other Instances

    The server sees: `LOGOUT_COMMAND`

    The server logs out the user from all devices except for the current one. A success message is sent back to the client once the user is logged out.

## Additional Notes on Wire Protocol ##

### Buffer Size ###
We chose a buffer size of 1024 as it encapsulates the maximum amount of information that we send over the wire at any given time
(1 (command) + 280 (max string input) * 3 + 4 (dividers) + 16 (time) = 861 bytes), while still being a power of 2.

### Locks ###
Our server uses locks to synchronize access to shared resources in a thread-safe manner. In particular, the `threading.Lock` object is used to guard access to the following shared resources:

- `accounts`: This dictionary stores the mapping between usernames and their corresponding password hashes. Passwords are hashed using the SHA256 algorithm. We add the lock whenever a user chooses to delete their account.

- `connected_clients`: This dictionary stores the list of all clients that are currently connected for a given user. This is used to facilitate the case where there are multiple instances of the same user being logged in simultaneously. We add the lock whenever a client connects or disconnects.

- `unsent_message_queue`: This dictionary stores the list of unsent messages for each user. Whenever a message is sent to a user who is not currently logged in, the message is added to the user's unsent message queue. Whenever the user logs in again, all unsent messages are sent to the user. We add the lock whenever a message is added to or removed from the queue.

- `messages`: This dictionary stores the message history between users. Whenever a message is sent, it is added to the message history of the sender and recipient. The lock is acquired whenever a message is added to the message history.

The locks ensure that only one thread at a time can modify the shared resources, preventing race conditions and ensuring that the data is consistent and correct.

## Implementation with gRPC ##
