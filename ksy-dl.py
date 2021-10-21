import atexit
import json
import os
import sys
import yaml

from bs4 import BeautifulSoup
from bs4.element import NavigableString
from http import HTTPStatus
from http.client import HTTPConnection, HTTP_PORT

BASE_DOMAIN = "formats.kaitai.io"
DB_FILE = os.path.join(os.path.dirname(__file__), 'format-db.json')

def load_ksy_db():
    db_fobj = open(DB_FILE, 'r')
    db_data = db_fobj.read()

    db_fobj.close()

    return json.loads(db_data)

ksy_cache = {}
ksy_db = load_ksy_db()

class FixDumper(yaml.Dumper):
    # https://github.com/yaml/pyyaml/issues/234#issuecomment-765894586
    def increase_indent(self, flow = False, *args, **kwargs):
        return super().increase_indent(flow = flow, indentless = False)

    # https://stackoverflow.com/a/33300001
    @staticmethod
    def str_presenter(dumper, data):
        if len(data.splitlines()) > 1:
            return dumper.represent_scalar('tag:yaml.org,2002:str', data, style = '|')
        return dumper.represent_scalar('tag:yaml.org,2002:str', data)

def sanitize_spec(ksy_spec):
    spec = ksy_spec.split('/')[-1]

    if spec not in ksy_db:
        print("[ - ] Unknown KSY specification passed: %s" % ksy_spec,
            file = sys.stderr)

        sys.exit(1)

    if '/' in ksy_spec:
        category = ksy_spec.split('/')[0]

        if len(category) != 0 and category != ksy_db[spec]:
            print("[ - ] Unknown KSY category : %s" % category,
                file = sys.stderr)

            sys.exit(1)

    return spec.strip('/')

def get_page(httpcon, ksy_spec):
    httpcon.request(
        'GET',
        '/' + sanitize_spec(ksy_spec) + '/'
    )

    response = httpcon.getresponse()

    if response.status == HTTPStatus.NOT_FOUND:
        print("[ - ] Unable to find '%s'. Server returned a 404." % ksy_spec,
            file = sys.stderr)

        sys.exit(1)
    elif response.status != HTTPStatus.OK:
        print("[ - ] Unable to fetch '%s'. Server returned status code: %d"
            % (spec, response.status), file = sys.stderr)

        sys.exit(1)

    return response.read().decode('utf-8')

def httpcon_setup():
    httpcon = HTTPConnection(BASE_DOMAIN, HTTP_PORT, timeout = 10)

    atexit.register(HTTPConnection.close, httpcon)

    return httpcon

def process_imports(httpcon, yaml_obj):
    for ksy_import in yaml_obj['meta']['imports']:
        if ksy_import in ksy_cache:
            continue

        bsoup = BeautifulSoup(get_page(httpcon, ksy_import), 'html.parser',
            multi_valued_attributes = None)

        process_page(httpcon, bsoup, ksy_import)

def process_code_section(httpcon, tag, ksy_spec):
    pre = tag.div.div.pre
    ksy_text = ""

    for subtag in pre:
        if subtag.string is None:
            continue

        ksy_text += subtag.string

    if ksy_spec not in ksy_cache:
        yaml_obj = yaml.safe_load(ksy_text)
        ksy_cache[ksy_spec] = yaml_obj
    else:
        yaml_obj = ksy_cache[ksy_spec]

    if 'meta' in yaml_obj and 'imports' in yaml_obj['meta']:
        process_imports(httpcon, yaml_obj)

def process_page(httpcon, bsoup, ksy_spec):
    for tag in bsoup.body:
        if ksy_spec.find('/') <= 0: # matches "/ksy_spec" and "ksy_spec"
            if tag.name == 'nav':
                pass
        if tag.name != 'section':
            continue

        if tag['id'] != 'format-ksy':
            continue
        else:
            process_code_section(httpcon, tag, ksy_spec)

def main(initial_ksy_spec):
    initial_ksy_spec = ksy_db[initial_ksy_spec] + '/' + initial_ksy_spec
    httpcon = httpcon_setup()
    bsoup = BeautifulSoup(get_page(httpcon, initial_ksy_spec), 'html.parser',
        multi_valued_attributes = None)

    process_page(httpcon, bsoup, initial_ksy_spec)

    for ksy_spec in ksy_cache:
        yaml_obj = ksy_cache[ksy_spec]
        ksy_spec = os.path.join(output_dir, ksy_spec.strip('/'))

        if 'meta' in yaml_obj and 'imports' in yaml_obj['meta']:

            # make all import paths local
            for idx, ksy_import in enumerate(yaml_obj['meta']['imports']):
                initial_ksy_dir = os.path.dirname(initial_ksy_spec.strip('/'))
                ksy_import = ksy_import.strip('/')

                if os.path.dirname(ksy_import) != initial_ksy_dir:
                    ksy_import = '../' + ksy_import
                else:
                    ksy_import = ksy_import.replace(initial_ksy_dir, '.')

                yaml_obj['meta']['imports'][idx] = ksy_import

        if not ksy_spec.endswith('.ksy'):
            ksy_spec += '.ksy'

        ksy_spec = ksy_spec.strip('/')

        if os.path.exists(ksy_spec):
            print("[ - ] './%s' already exists. Skipping..." % ksy_spec,
                file = sys.stderr)

            continue
        else:
            os.makedirs(
                os.path.dirname(ksy_spec),
                mode = 0o755,
                exist_ok = True
            )

        with open(ksy_spec, 'w') as ksy_fobj:
            ksy_fobj.write(
                yaml.dump(yaml_obj, sort_keys = False, Dumper = FixDumper)
            )

    httpcon.close()

yaml.add_representer(str, FixDumper.str_presenter)

try:
    # this first call to sanitize_spec will verify and extract
    # the spec name if the category is present in the input str
    query = sanitize_spec(sys.argv[1])
    output_dir = sys.argv[2]
except IndexError:
    print("usage: python3 ksy-dl.py QUERY OUTPUT_DIR",
        file = sys.stderr)
    sys.exit(1)

main(query)