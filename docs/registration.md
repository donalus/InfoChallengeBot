# How registration works 

Registration is provided through a chatbot interface. The current implementation is a very basic finite state machine. 
It isn't a fancy nlp or ml model. The initial goal was to use [Rasa](https://rasa.com/), but Discord is not implemented 
in a way that made that easy. However, in the future the goal is to move to using Rasa's REST API to have a more 
robust conversational UI. 

## Registration Process

This is the process that happens when a new user joins the Discord server:

1. InfoChallengeBot direct messages the user with a greeting and asks for their email address.
2. The user responds with their email address.
3. InfoChallengeBot checks the database for the email address and asks the user to confirm.
4. If the user confirms that it is their registration, InfoChallengeBot adds the correct Roles to the user.
5. InfoChallengeBot lets the user know that their registration is complete.

Unsuccessful paths include an email not found:

1. InfoChallengeBot direct messages the user with a greeting and asks for their email address.
2. The user responds with their email address.
3. InfoChallengeBot cannot find the email address.
4. InfoChallengeBot asks the user if they would like to try another email address.
5. If the user says "yes", then InfoChallengeBot asks for the email address.
6. If the user says "no", then InfoChallengeBot tells them to contact the support email address.

Unsuccessful paths include or a duplicate email address:

1. InfoChallengeBot direct messages the user with a greeting and asks for their email address.
2. The user responds with their email address.
3. InfoChallengeBot finds that the email has already been used to register by another participant.
4. InfoChallengeBot tells them to contact the support email address.

## Testing Registration

The bot provides the following commands to help with testing registration:

- `/reg reset` - This command will reset a user's registration status and remove any added roles.

