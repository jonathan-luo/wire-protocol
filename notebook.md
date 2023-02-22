# Engineering Notebook #

## Connecting to the Server ##
When the user runs the client program, they will be prompted to enter the IP address of the server, which they can then connect to.

We got the computers to communicate by finding the IP address of the server under Mac > Settings > Wifi. One solution was to hardcode this address into the client.py file of the client computer. However, we ended up doing something more dynamic, by allowing users to specify the server IP address that they would connect to as a command-line prompt.

## Logging In/Creating an Account ##
Once logged in and connected to the server, the user will be prompted to enter their username.
If the username exists in the system, then they must enter their password. They have up to 3 tries to enter the correct password. They also have the option to quit, which would then alert the server to close this client. If they correctly enter their password, then they are logged in.
If the username doesn’t exist in the system, then they must create a new password and then enter a confirmation password to make a new account. Whenever they enter the wrong confirmation password, they have the option to quit or retry a different password.

- Onboarding

    The server sees: `LOGIN_COMMAND [args]`

## Selection Screen ##
Once successfully logged in, the user will be greeted with a welcome message, as well as the notification of how many of the same account are logged into the system. They will receive all the undelivered messages. Then, they will receive a selection screen for what they want to do next. The menu consists of:

- List All Accounts

    The server sees: `VIEW_USERS_COMMAND [arg : str = '*']`

    The method by which users can specify their search criteria is as follows: Once they select "View Users" as their desired task, a prompt pops up asking if they would like to submit a wildcard query for specific users. Leaving this prompt blank (i.e., by simply pressing Enter) will return all active users other than the current user, if any. Otherwise, the user can specify, using GLOB wildcard syntax, usernames that they wish to query for. On the backend, searching is done by converting the GLOB query into Regex using the `fnmatch.translate` function. Then, that regex pattern is compiled and used to filter over all active users (other than the current user). If no matches are found, "No users found." is printed, which is the same behavior as when there are no other active users at all.

- Send A Message

    The server sees: `SEND_MESSAGE_COMMAND [username] [message]`

    When the user logs in, any undelivered messages that were sent to them while they were offline are sent to them. When the user selects "Send A Message," they are prompted to enter the username of the recipient and the message they want to send. If the recipient is currently logged in, the message is immediately delivered to all of their connected devices. Otherwise, the message is added to a queue for the recipient and will be delivered the next time they log in. A success message is sent back to the client once the message is sent.

    When a message is sent from one user to another, it is either immediately delivered to the recipient's connected clients, or it is added to a queue to be delivered the next time the recipient logs in. If the recipient is currently logged in, the `deliver_new_message()` function is called to deliver the message to all of their connected devices. If the recipient is not logged in, the message is added to a queue for the recipient in the `unsent_message_queue` dictionary. Once the recipient logs in, all of their undelivered messages are immediately sent to them, including messages that were in the queue. The message is also stored in the message history `messages` dictionary on the server.

- Delete Account

    The server sees: `8`

- Quit

    The server sees: `9`

In addition to these selectable operations for users, there also exist hidden operations such as the following, which are also part of our wire protocol definition, but not explicitly available for the user to invoke. These are often part of validating user input, such as ensuring that users send messages only to registered users, or that they can only delete an account when it is only logged into one device.

- Verify Registered User

    The server sees: `CHECK_ACCOUNT_COMMAND [username]`

    The server checks if the username exists and sends a message back to the client indicating whether or not the account exists.

- Verify Account Only Logged In On One Device

    The server sees: `MULTIPLE_LOGIN_COMMAND`

    The server checks if the user has logged in from multiple devices and sends a message back to the client indicating whether or not multiple logins exist.

- Log Out All Other Instances

    The server sees: `LOGOUT_COMMAND`

    The server logs out the user from all devices except for the current one. A success message is sent back to the client once the user is logged out.

## Additional Notes on Wire Protocol ##
We chose a buffer size of 1024 as it encapsulates the maximum amount of information that we send over the wire at any given time
(1 (command) + 280 (max string input) * 3 + 4 (dividers) + 16 (time) = 861 bytes), while still being a power of 2.

Our server uses locks to synchronize access to shared resources in a thread-safe manner. In particular, the `threading.Lock` object is used to guard access to the following shared resources:

- `connected_clients`: This dictionary stores the list of all clients that are currently connected for a given user. This is used to prevent multiple instances of the same user from being logged in simultaneously. We add the lock whenever a client connects or disconnects.

- `unsent_message_queue`: This dictionary stores the list of unsent messages for each user. Whenever a message is sent to a user who is not currently logged in, the message is added to the user's unsent message queue. Whenever the user logs in again, all unsent messages are sent to the user. We add the lock whenever a message is added to or removed from the queue.

- `messages`: This dictionary stores the message history between users. Whenever a message is sent, it is added to the message history of the sender and recipient. The lock is acquired whenever a message is added to the message history.

The locks ensure that only one thread at a time can modify the shared resources, preventing race conditions and ensuring that the data is consistent and correct.