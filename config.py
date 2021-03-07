class Config():
    def __init__(self, cfg_file='sett.cfg'):
        self.sett = {"IP": "127.0.0.1"}
        self.load(cfg_file)

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

    def save(self, cfg_file='sett.cfg'):
        with open(cfg_file, 'w') as fp:
            for key, val in self.sett.items():
                fp.write(f"{key} = {val}\n")