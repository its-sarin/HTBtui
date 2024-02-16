## HTBtui

HTBtui is a "terminal user interface" for interacting with the Hack the Box api.

![Screenshot from 2024-02-15 14-50-56](https://github.com/its-sarin/HTBtui/assets/1649588/863fc447-c4f4-4f2f-9dbe-181755ca61c3)

### Features

The following features are currently supported:
- Player statistics
- Player seasonal statistics
- Player activity
- Current, retired, and seasonal machine listing
- Starting, stopping, and resetting current, retired, and seasonal machines
- Flag submission for current, retired, and seasonal machines
- Machine statistics and user-submitted difficulty rating
- HTB vpn connection status with IP address (with click-to-copy functionality)
- Active machine status with IP address (with click-to-copy functionality)

![Screenshot from 2024-02-15 14-54-49](https://github.com/its-sarin/HTBtui/assets/1649588/94a488fe-e39c-48bb-9769-af38b202a133)

---

### Configuration

HTBtui requires a Hack the Box API token in order to function. To generate an API token, go to your Hack the Box profile settings found here: https://app.hackthebox.com/profile/settings

*[Note: if you've previously configured "HTB cli", you can skip this part as the token and the environment variable are the same]*

Click on "Create App Token":

![Screenshot from 2024-02-15 18-49-51](https://github.com/its-sarin/HTBtui/assets/1649588/5b264b7e-5952-427d-899d-cbaf2fc4c0f1)

The generated token will only be revealed to you one time, so be sure to keep a record of it in a secure place.

This token will need to be added as an environment variable named "HTB_TOKEN" to your `.zshrc` or `.bashrc` file:
```
echo "export HTB_TOKEN=<TOKEN VALUE> | tee -a ~/.zshrc
```

Reinitialize your `.zshrc` or `.bashrc` file: 
```
. ~/.zshrc
```

### Installation

Clone the repo:

```
git clone https://github.com/its-sarin/HTBtui.git
```

Install requirements via pip3:
```
pip3 install -r requirements.txt
```

Now you can run HTBtui!
```
python3 htbtui.py
```

