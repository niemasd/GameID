# helper class to handle ISO 9660 disc images
class ISO9660:
    # initialize ISO handling
    def __init__(self, fn, console, bufsize=DEFAULT_BUFSIZE):
        if fn.split('.')[-1].strip().lower() in {'7z', 'zip'}:
            error("%s files are not yet supported for %s games" % (fn.split('.')[-1].strip().lower(), console))
        self.fn = abspath(expanduser(fn)); self.size = getsize(fn); self.console = console
        if fn.lower().endswith('.cue'):
            f_cue = open_file(fn, 'rt', bufsize=bufsize)
            self.bins = ['%s/%s' % ('/'.join(abspath(expanduser(fn)).split('/')[:-1]), l.split('"')[1].strip()) for l in f_cue if l.strip().lower().startswith('file')]
            f_cue.close()
            self.size = sum(getsize(b) for b in self.bins)
            self.f = open_file(self.bins[0], 'rb', bufsize=bufsize)
        else:
            self.f = open_file(self.fn, 'rb', bufsize=bufsize)
        if (self.size % 2352) == 0:
            self.block_size = 2352
        elif (self.size % 2048) == 0:
            self.block_size = 2048
        else:
            error("Invalid disc image block size: %s" % fn)

        # PSX raw image starts at 0x18: https://github.com/cebix/ff7tools/blob/21dd8e29c1f1599d7c776738b1df20f2e9c06de0/ff7/cd.py#L30-L40
        if self.console == 'PSX' and self.block_size == 2352:
            self.block_offset = 0x18
        else:
            self.block_offset = 0 # most console disc images start at the beginning

        # read PVD: https://wiki.osdev.org/ISO_9660#The_Primary_Volume_Descriptor
        self.f.seek(self.block_offset + (16 * self.block_size)); self.pvd = self.f.read(2048)

    # get system ID
    def get_system_ID(self):
        system_ID = self.pvd[8 : 40]
        try:
            return system_ID.decode().strip()
        except:
            return system_ID

    # get volume ID
    def get_volume_ID(self):
        volume_ID = self.pvd[40 : 72]
        try:
            return volume_ID.decode().strip()
        except:
            return volume_ID

    # get publisher ID
    def get_publisher_ID(self):
        publisher_ID = self.pvd[318 : 446]
        try:
            return publisher_ID.decode().strip()
        except:
            return publisher_ID

    # get data preparer ID
    def get_data_preparer_ID(self):
        data_preparer_ID = self.pvd[446 : 574]
        try:
            return data_preparer_ID.decode().strip()
        except:
            return data_preparer_ID

    # get UUID (usually YYYY-MM-DD-HH-MM-SS-?? but not always a valid date)
    def get_uuid(self):
        # find UUID (usually offset 813 of PVD, but could be different)
        uuid_start_ind = 813
        for i in range(813, 830):
            if self.pvd[i] in ISO966O_UUID_TERMINATION:
                uuid_start_ind = i - 16; break
        uuid = self.pvd[uuid_start_ind : uuid_start_ind + 16]

        # try to parse as text (if it fails, just return the raw bytes)
        try:
            uuid = uuid.decode()
        except:
            return uuid

        # add dashes to UUID text and return: YYYYMMDDHHMMSS?? --> YYYY-MM-DD-HH-MM-SS-??
        out = uuid[:4]
        for i in range(4, len(uuid), 2):
            out = out + '-' + uuid[i:i+2]
        return out

    # parse filenames: https://wiki.osdev.org/ISO_9660#Recursing_from_the_Root_Directory
    def get_filenames(self, only_root_dir=True):
        root_dir_lba = unpack('<I', self.pvd[156 +  2 : 156 +  6])[0]
        root_dir_len = unpack('<I', self.pvd[156 + 10 : 156 + 14])[0]
        to_explore = [('/', root_dir_lba, root_dir_len)]; files = list()
        while len(to_explore) != 0:
            curr_path, curr_lba, curr_len = to_explore.pop()
            self.f.seek(self.block_offset + (curr_lba * self.block_size))
            curr_data = self.f.read(curr_len); i = 0
            while i < len(curr_data):
                next_len = curr_data[i + 0]
                if next_len == 0:
                    break
                next_ext_attr_rec_len = curr_data[i + 1]
                next_lba = unpack('<I', curr_data[i + 2 : i + 6])[0]
                next_data_len = unpack('<I', curr_data[i + 10 : i + 14])[0]
                next_rec_date_time = curr_data[i + 18 : i + 25]
                next_file_flags = curr_data[i + 25]
                next_file_unit_size = curr_data[i + 26]
                next_interleave_gap_size = curr_data[i + 27]
                next_vol_seq_num = unpack('<H', curr_data[i + 28 : i + 30])[0]
                next_name_len = curr_data[i + 32]
                next_name = curr_data[i + 33 : i + 33 + next_name_len]
                if next_name not in {b'\x00', b'\x01'}:
                    try:
                        next_name = next_name.decode()
                        if next_name.endswith(';1'):
                            next_path = '%s%s' % (curr_path, next_name[:-2])
                        else:
                            next_path = '%s%s/' % (curr_path, next_name)
                        next_tup = (next_path, next_lba, next_len)
                        if not next_path.endswith('/'):
                            files.append(next_tup)
                        elif not only_root_dir:
                            #to_explore.append(next_tup) # doesn't work
                            raise NotImplementedError("Currently only supports root directory")
                    except:
                        pass # skip trying to load filename that's not a valid string
                i += next_len
        return files
