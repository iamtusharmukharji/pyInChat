import json

class CredLoader:
    def __init__(self, cred_file):
        self.cred_file = cred_file

        self.credentials = self.load_credentials()
        
        self.db_creds = self.credentials.get('database', {})
        self.smtp_creds = self.credentials.get('smtp', {})

    def load_credentials(self):
        with open(self.cred_file, 'r') as file:
            return json.load(file)

    

fileName = './creds.json'
cred_loader = CredLoader(fileName)
print(cred_loader.db_creds)