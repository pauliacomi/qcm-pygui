class Config():
    def __init__(self, cfg_file='settings.cfg'):
        self.file = cfg_file
        self.sett = {
            "instrument": "TCPIP::127.0.0.1::HISLIP",
            "data_folder": "current_data",
        }
        self.load(self.file)

    def get(self, key):
        return self.sett[key]

    def set(self, key, val):
        self.sett[key] = val

    def load(self, cfg_file):
        try:
            for line in open(cfg_file):
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
        with open(self.file, 'w') as fp:
            for key, val in self.sett.items():
                fp.write(f"{key} = {val}\n")