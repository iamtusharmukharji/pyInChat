

class WSConnectionManager:
    def __init__(self):
        self.user_connection_map = {}
        self.active_connections = 0

    def add_connection(self, user_id, ws_instance):
        self.user_connection_map[user_id] = ws_instance
        self.active_connections += 1

    def remove_connection(self, user_id):
        if user_id in self.user_connection_map:
            del self.user_connection_map[user_id]
            self.active_connections -= 1
    def get_connection(self, user_id):
        return self.user_connection_map.get(user_id, None)
    

ws_manager = WSConnectionManager()