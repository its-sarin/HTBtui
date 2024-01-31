import os

class APIToken:
    def __init__(self, token_name):
        # print(f'Checking for {token_name} in environment variables')        
        self.token_name = token_name
        self.token = os.environ.get(self.token_name) if self.token_name in os.environ else None

        if self.token is None:
            raise ValueError(f'{self.token_name} not found in environment variables')
        elif len(self.token.split('.')) != 3:
            raise ValueError(f'Invalid {self.token_name} found in environment variables. Please check your API key or generate a new one.')

    def get_token(self):
        # print(f'Found {self.token_name} in environment variables')
        return self.token