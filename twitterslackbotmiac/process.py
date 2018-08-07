from os import environ
import re
from threading import Timer
import json
from json import loads
from tweepy.api import API
from tweepy.auth import OAuthHandler
from slackclient import SlackClient
import schedule, time
import config
# instantiate Slack client
slack_client = SlackClient(config.SLACK_BOT_TOKEN)
# starterbot's user ID in Slack: value is assigned after the bot starts up
starterbot_id = None

# constants
RTM_READ_DELAY = 1 # 1 second delay between reading from RTM
EXAMPLE_COMMAND = "do"
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"

def trends(channel='assignment1', scheduled=True):
    '''
    consumer_key = environ.get('consumer_key', None)
    consumer_secret = environ.get('consumer_secret', None)
    access_token = environ.get('access_token', None)
    access_token_secret = environ.get('access_token_secret', None)
    '''

    auth = OAuthHandler(config.consumer_key, config.consumer_secret)
    auth.set_access_token(config.access_token, config.access_token_secret)
    api = API(auth)

    # Where On Earth ID for Pasig is 1187115.
    # Where On Earth ID for Worldwide 1.
    WOE_ID = 1

    trends = api.trends_place(WOE_ID)

    trends = json.loads(json.dumps(trends, indent=1))

    trendy = []
    for trend in trends[0]["trends"]:
        trendy.append((trend["name"]))

    trending = ', \n'.join(trendy[:10])

    if scheduled:
        slack_client.api_call(
            "chat.postMessage",
            channel=channel,
            text=trending
        )
    else:
        return trending


def parse_bot_commands(slack_events):

    for event in slack_events:
        if event["type"] == "message" and not "subtype" in event:
            user_id, message = parse_direct_mention(event["text"])
            if user_id == starterbot_id:
                return message, event["channel"]
    return None, None

def parse_direct_mention(message_text):

    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)

def handle_command(command, channel):

    # Default response is help text for the user
    default_response = "Not sure what you mean. Try *{}*.".format(EXAMPLE_COMMAND)

    # Finds and executes the given command, filling in response
    response = None
    scheduled = False
    # This is where you start to implement more commands!

    if command.startswith(EXAMPLE_COMMAND):
        response = "Sure...write some more code then I can do that!"
    else:
        response = trends(channel,scheduled)

    # Sends the response back to the channel
    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=response or default_response
    )
if __name__ == "__main__":
    if slack_client.rtm_connect(with_team_state=False):
        print("Starter Bot connected and running!")
        # Read bot's user ID by calling Web API method `auth.test`
        starterbot_id = slack_client.api_call("auth.test")["user_id"]
        schedule.every(24).hours.do(trends)
        while True:
            schedule.run_pending()
            time.sleep(RTM_READ_DELAY)
            command, channel = parse_bot_commands(slack_client.rtm_read())
            if command:
                handle_command(command, channel)
            time.sleep(RTM_READ_DELAY)
    else:
        print("Connection failed. Exception traceback printed above.")
