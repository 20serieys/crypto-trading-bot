import os
from slack_sdk import WebClient
from flask import Flask, request
import requests

CARD_TEMPLATE = {
    "text":"",
    "blocks":[],
    "attachments" : []
}

class SlackMessage():
    """
    Class for streamlining the creation and sending of messages on Slack Channels

    Args:
        webhook_url (str): incoming webhook URL for Slack channel. This can be created in the connectors section within the Slack app
        http_timeout (int, optional): time in seconds before request times out. Defaults to 60.
    """

    def __init__(self, webhook_url: str, http_timeout: int = 60):
        self.webhook_url = webhook_url
        self.http_timeout = http_timeout
        self.last_response = None
        # Instantiate the component parts of the adaptive card
        self.blocks = []
        self.attachments = []
        self.slackapi = {}
        self.actions = {}

    def setTitle(self, title: str):
        """
        Set the text for the title

        Args:
            title (str): title of message that will be in bold
        """
        new_title = {
			"type": "header",
			"text": {
				"type": "plain_text", # find syntax for bold
				"text": title
			}
		}
        self.blocks.append(new_title)

        return self

    def setText(self, text: str, bullets: list = []):
        """
        Set the text block of the message; note this overwrites any text previously set

        Args:
            text (str): text body of message.
            bullets (list, optional): list of strings that will display as unordered bulletpoints. Defaults to [].

        Formatting:
            Note the text can be formatted in the following ways:
            - Carriage returns can be given by backslash r
            - Unordered bullets can be given by "-". It is however recommended to use the bullets argument
            - URLs can be given using "[Title](url)"
        """
        formatted_bullets = "\r - " + "\r - ".join(bullets) if bullets else ""
        self.blocks.append({                        
            "type": "section",
            "text": { 
                "type":"mrkdwn",
                "text":text + formatted_bullets
            }
        })
        return self

    def setFact(self, title: str, value: str):
        """
        Sets facts with key, value pairs

        Args:
            title (str): title of fact or attribute that will be in bold
            value (str): associated value
        """
        existing_facts = self.body.get('facts', [])

        new_facts = [
            *[fact for fact in existing_facts if fact['title']!=title],
            {'title': title, 'value':value}
        ]

        self.body['facts'] = new_facts

        return self

    def setLink(self, title: str, url: str):
        """
        Create buttons in message to redirect the user elsewhere

        Args:
            title (str): text that appears in the button eg: "Go to Google"
            url (str): target url eg: "https://google.co.uk"
        """

        new_btn = {
            "type": "actions",
            "elements": [
              {
					"type": "button",
					"text": {
						"type": "plain_text",
						"text": title
					},
                    "url" : url,
				}
            ]
        }
        self.blocks.append(new_btn)

        return self

    def id_from_email(self, usr_email:str, bot_token:str):
        client = WebClient(token = bot_token)
        usr = client.users_lookupByEmail(email = usr_email)
        return usr['user']['id']


    def setMention(self, email : str, bot_token: str):
        """
        Sets people who will be notified in message

        Args:
            email (str): email of tagged individual linked with Slack channel
            name (str): name of tagged individual
        """
        user_id = self.id_from_email(usr_email = email, bot_token = bot_token)
        text_mention = "<@" +user_id+ ">"
        self.setText(text_mention)

        return self
        
    def setWebhookUrl(self, webhook_url: str):
        """
        Overwrites the webhook url; can be used to send the same message to another channel

        Args:
            webhook_url (str): incoming webhook url for Slack channel 
        """
        self.webhook_url = webhook_url
        return self

    def _create_card(self) -> dict:
        """
        Combines all the elements to create adaptive card dictionary
        """
        card = CARD_TEMPLATE.copy()

        card['blocks'] = self.blocks
        card['attachments'] = self.attachments

        return card



    def send(self) -> bool:
        """
        Sends the message to the specified Slack Channel

        Raises:
            Exception: if response status code does not indicate message

        Returns:
            bool: if successful returns True
        """
        # headers = {"Content-Type": "application/json"}  # Are headers useful ?
        payload = self._create_card()

        response = requests.post(
            self.webhook_url,
            json=payload,
            # headers=headers,
            timeout=self.http_timeout
        )
        self.last_response = response

        if response.status_code == requests.codes.ok:
            return True
        else:
            raise Exception(response.text)



    # Specific to strategied
    def buy_message(self, balance, coin_name:str):
        self.reset_payload()
        title = "Nouvel achat sur "+coin_name
        self.setText(title)
        corps = f'Balance : {balance}$'
        self.setText(corps)
        # self.setMention(email,bot_token)
        self._create_card()
        self.send()
        

    def sell_message(self, balance, coin_name:str):
        self.reset_payload()
        title = "Nouvelle vente sur "+ coin_name
        self.setText(title)
        corps = f'Balance : {balance}$'
        self.setText(corps)
        # self.setMention(email,bot_token)
        self._create_card()
        self.send()
        


    def reset_payload(self):
        self.blocks = []
        self.attachments = []
        self.slackapi = {}
        self.actions = {}

    def send_text_message(self, message:str):
        self.reset_payload()
        self.setText(message)
        self._create_card()
        self.send()