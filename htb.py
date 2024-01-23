import requests
import os
from rich.console import Console
from rich.table import Table
from rich.layout import Layout
from rich import box

# Set your Hack The Box API key
# Retrieve API key from environment variable
api_key = os.environ['HTB_API_KEY']

class HTBClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://labs.hackthebox.com"
        self.info_endpoint = "/api/v4/user/info"
        self.profile_endpoint = "/api/v4/profile/"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "HTBClient/1.0.0"
        }
        self.ranks = [
            "Noob",
            "Script Kiddie",
            "Hacker",
            "Pro Hacker",
            "Elite Hacker",
            "Guru",
            "Omniscient"
        ]
        self.id = None
        self.name = None
        self.points = None
        self.user_owns = None
        self.system_owns = None
        self.rank_progress = None
        self.user_name = None
        self.user_rank = None
        self.user_points = None
        self.user_user_owns = None
        self.user_system_owns = None
        self.user_rank_progress = None

    # def get_info(self):
    #     response = requests.get(self.base_url + self.info_endpoint, headers=self.headers)
    #     if response.status_code == 200:
    #         data = response.json()
    #         print(data)
    #         self.name = data['info']['name']
    #         self.rank = data['info']['rank_id']
    #         self.points = data['info']['points']
    #         self.user_owns = data['info']['user_owns']
    #         self.system_owns = data['info']['system_owns']
    #         self.rank_progress = data['info']['current_rank_progress']
    #     else:
    #         print(f"Error: {response.status_code} - {response.text}")

    def get_profile(self):
        if self.id is None:
            self.get_user_id()
        response = requests.get(self.base_url + self.profile_endpoint + str(self.id), headers=self.headers)
        if response.status_code == 200:
            data = response.json()
            self.user_name = data['profile']['name']
            self.user_rank = data['profile']['rank_id']
            self.ranking = data['profile']['ranking']
            self.user_points = data['profile']['points']
            self.user_user_owns = data['profile']['user_owns']
            self.user_system_owns = data['profile']['system_owns']
            self.user_rank_progress = data['profile']['current_rank_progress']

            return data
        else:
            print(f"Error: {response.status_code} - {response.text}")

    def get_user_id(self):
        response = requests.get(self.base_url + self.info_endpoint, headers=self.headers)
        if response.status_code == 200:
            data = response.json()
            self.id = data['info']['id']

            return self.id
        else:
            print(f"Error: {response.status_code} - {response.text}")

    def print_profile(self):

        table = Table(title="Profile", title_justify="left", box=box.ASCII, show_header=False, show_footer=False, expand=True)

        table.add_column(style="chartreuse1 bold", no_wrap=True)
        table.add_column(style="chartreuse1")

        table.add_row("Name", self.user_name)
        table.add_row("Rank", self.ranks[self.user_rank-1])
        # table.add_row(f"% to {self.ranks[self.user_rank]}", str(self.user_rank_progress))
        table.add_row("Rank progress", str(self.user_rank_progress))
        table.add_row("Ranking", str(self.ranking))        
        table.add_row("Points", str(self.user_points))
        table.add_row("User Owns", str(self.user_user_owns))
        table.add_row("System Owns", str(self.user_system_owns))
        
        return table

        # console = Console()
        # console.print(table, justify="center")
        # print(f"Name: {self.user_name}")
        # print(f"Rank: {self.user_rank}")
        # print(f"Ranking: {self.ranking}")
        # print(f"Points: {self.user_points}")
        # print(f"User Owns: {self.user_user_owns}")
        # print(f"System Owns: {self.user_system_owns}")
        # print(f"Rank Progress: {self.user_rank_progress}")

# htb = HTBClient(api_key)
# htb.get_profile()
# htb.print_profile()