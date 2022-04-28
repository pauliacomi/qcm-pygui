"""
Configuration and settings for the program.
Loaded into memory and stored in a configuration file.
"""


class Config():
    """A simple config class."""
    def __init__(self, cfg_file='settings.cfg'):
        self.file = cfg_file
        self.sett = {
            "instrument": "TCPIP::127.0.0.1::HISLIP",
            "data_folder": "current_data",
            "start": 9920000,
            "stop": 10020000,
        }
        self.load(self.file)

    def get(self, key):
        """Get a setting value."""
        return self.sett.get(key, None)

    def set(self, key, val):
        """Set a setting value."""
        self.sett[key] = val

    def load(self, cfg_file):
        """Load settings file from disk."""
        try:
            for line in open(cfg_file, encoding="utf8"):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                keyvals = line.split('=', 1)
                if not len(keyvals) == 2:
                    continue
                key, val = map(str.strip, keyvals)

                if key in self.sett:
                    self.sett[key] = val
        except:
            pass

    def save(self):
        """Save settings file from disk."""
        with open(self.file, 'w', encoding="utf8") as fp:
            for key, val in self.sett.items():
                fp.write(f"{key} = {val}\n")
