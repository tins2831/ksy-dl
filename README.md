# ksy-dl
Downloads `.ksy` files and their dependecies straight from the official kaitai-struct [format gallery](http://formats.kaitai.io/).

This tool will:
* Fetch any of the official specifications
* Fetch only their dependencies
* Organize the specifications into separate directories based on the category of the specification
* Rewrite the import paths of the dependencies so that they use relative paths

This makes it easy to include, modify, and share [official and community created](https://github.com/kaitai-io/kaitai_struct_formats) kaitai-struct specifications in individual projects.

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
$ python3 ksy-dl.py "network/pcap" .
$ python3 ksy-dl.py "pcap" ../kaitai # will create non-existing directories too
$ python3 ksy-dl.py "/network/pcap" network/
$ python3 ksy-dl.py "pcap.ksy" .
$ python3 ksy-dl.py "google_protobuf" .
```

### Auto-updating the database
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
