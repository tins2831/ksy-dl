# KSY-DL
Downloads `.ksy` files and their dependecies straight from the official kaitai-struct [format gallery](http://formats.kaitai.io/).

### Requirements
* [PyYAML](https://pyyaml.org/)
* [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/bs4/)
```
$ git clone https://github.com/tins2831/urlgrep.git
$ cd ksy-dl
$ python3 -m pip install --user -r requirements.txt
```

### Usage
```
usage: python3 ksy-dl.py QUERY OUTPUT_DIR
...

Examples:
$ python3 ksy-dl.py "network/pcap"
$ python3 ksy-dl.py "pcap"
$ python3 ksy-dl.py "/network/pcap"
$ python3 ksy-dl.py "pcap.ksy"
# python3 ksy-dl.py "google_protobuf"
```

### Auto-updating the DB
First, clone the kaitai format gallery from github:
```
$ git clone https://github.com/kaitai-io/kaitai_struct_formats.git
```

Then adjust and append this to your crontab:
```
# Update ksy-dl format db.
# Runs every day at midnight.
00 00 * * * (KAITAI_FMT_REPO=<path to repo> <path to ksy-dl repo>/tools/db-update.sh)
```