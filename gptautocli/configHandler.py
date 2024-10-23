import configparser
import os
from openai import OpenAI

# Determine the appropriate config path based on the operating system
def get_config_path():
    return os.path.expanduser('~/.gptautocli.config')

config_path = get_config_path()
config = configparser.ConfigParser()

class ConfigHandler:
    def __init__(self, user_interface):
        self.user_interface = user_interface
        self.setup_api_key()
        self.setup_command_risk()

    # allows the user to decide what threshold of risk a command needs before requiring confirmation
    def setup_command_risk(self):
        if 'Command_Risk' not in config['DEFAULT']:
            prompt_message = (
                "A separate AI model evaluates each command generated by gptautocli to determine how risky it is on a scale of 1-5. \n"
                "For example 'ls' would be a 1, while 'rm -rf *' would be a 5. \n"
                "For a more in depth explanation of each risk level and how this system works, see the README (https://github.com/BSchoolland/gptautocli)\n"
                "Entering 0 will require confirmation for all commands, while 6 will run all commands without confirmation. \n"
                "Please enter the threshold of risk that a command must be below to be executed without confirmation (1-5)"
            )
            command_risk = self.user_interface.dialog(prompt_message)
            if command_risk.isdigit() and 0 <= int(command_risk) <= 6:
                config['DEFAULT']['Command_Risk'] = command_risk
                with open(config_path, 'w') as configfile:
                    config.write(configfile)
                self.user_interface.info("Command risk threshold saved successfully.")
            else:
                self.user_interface.error("Invalid command risk threshold entered. Please enter a number between 0 and 6.")
                exit(1)
        else:
            config.read(config_path)
        

    def setup_api_key(self):
        """
        Setup the OpenAI API key
        """
        # Read the existing configuration if it exists
        if os.path.exists(config_path):
            config.read(config_path)
        
        if 'OpenAI_API_Key' not in config['DEFAULT']:
            # Determine the prompt message based on the operating system
            
            prompt_message = (
                "gptautocli requires a valid OpenAI API key (which will not be shared with anyone) to function. \n"
                "Please add your key to ~/.gptautocli.config and restart the program or enter it here"
            )
            
            api_key = self.user_interface.dialog(prompt_message)
            
            # Confirm that the key works
            client = OpenAI(api_key=api_key)
            try:
                if self.test_client(client):
                    self.user_interface.info("API key verified successfully.")
                else:
                    self.user_interface.error("You entered: " + api_key)
                    self.user_interface.error("API key verification failed. Please check your API key and try again.")
                    exit(1)
            except Exception as e:
                self.user_interface.error("You entered: " + api_key)
                self.user_interface.error("API key verification failed. Please check your API key and try again.")
                print(f"Error: {type(e).__name__}, {str(e)}")
                exit(1)

            # Update the configuration with the new API key
            config['DEFAULT']['OpenAI_API_Key'] = api_key
            with open(config_path, 'w') as configfile:
                config.write(configfile)
            self.user_interface.info("API key saved successfully.")
        else:
            config.read(config_path)
    
    def test_client(self, client):
        """
        Test the OpenAI API client by sending a simple prompt

        Parameters
        ----------
        client : OpenAI
            The OpenAI API client

        Returns
        -------
        bool
            True if the client is working, False otherwise
        """
        # Add user input to the conversation history
        conversation_history = [{"role": "user", "content": "Hi"}]

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=conversation_history
        )

        # Get the response message
        response_message = response.choices[0].message.content

        # Add the response to the conversation history
        conversation_history.append({"role": "assistant", "content": response_message})

        return bool(response_message)