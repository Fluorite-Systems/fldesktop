class Communicator:
    def __init__(self):
        self.services = []
        self.signal_subs = []

    def register(self, name: str, actions: dict):
        "Register in communicator"

        self.services.append((name, actions))

    def request(self, name: str, action: str, *args, **kwargs):
        "Requests something from service"

        r = None

        for s in self.services:
            if s[0] == name:
                if action in s[1]:
                    r = s[1][action](*args, **kwargs)
        
        return r

    def subscribe(self, signal: str, action):
        "Subscribe to some signal"

        self.signal_subs.append(
            {
                "signal": signal,
                "action": action
            }
        )

    def unsubscribe(self, action):
        "Unsubscribe action from signal"

        for i in self.signal_subs:
            if i["action"] == action:
                self.signal_subs.remove(i)
    
    def emit(self, signal: str, *args):
        "Emit a signal"

        for i in self.signal_subs:
            if i["signal"] == signal:
                i["action"](*args)
