import atexit
import os
import sys
import re
import yaml

from bs4 import BeautifulSoup
from bs4.element import NavigableString
from http import HTTPStatus
from http.client import HTTPConnection, HTTP_PORT

BASE_DOMAIN = "formats.kaitai.io"
SANITIZE_RGX = "[A-Za-z0-9._\\-]+/([A-Za-z0-9._\\-]+)"

ksy_cache = {}

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
    match = re.search(SANITIZE_RGX, ksy_spec)

    if match is None:
        print("[ - ] Invalid KSY specification passed: %s" % ksy_spec,
            file = sys.stderr)

        sys.exit(1)

    return re.sub("\\.\\w+$", "", match[1])

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
        if tag.name != 'section':
            continue

        if tag['id'] != 'format-ksy':
            continue
        else:
            process_code_section(httpcon, tag, ksy_spec)

def main(initial_ksy_spec):
    httpcon = httpcon_setup()
    bsoup = BeautifulSoup(get_page(httpcon, initial_ksy_spec), 'html.parser',
        multi_valued_attributes = None)

    process_page(httpcon, bsoup, initial_ksy_spec)

    for ksy_spec in ksy_cache:
        yaml_obj = ksy_cache[ksy_spec]

        if 'meta' in yaml_obj and 'imports' in yaml_obj['meta']:

            # make all import paths local
            for idx, ksy_import in enumerate(yaml_obj['meta']['imports']):
                initial_ksy_dir = os.path.dirname(initial_ksy_spec.strip('/'))
                ksy_import = ksy_import.strip('/')

                if os.path.dirname(ksy_import) != initial_ksy_dir:
                    continue

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
main(sys.argv[1])