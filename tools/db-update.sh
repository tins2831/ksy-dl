#!/usr/bin/env bash

# Updates the database for which ksy-dl queries the name of a
# ksy specification.

SCRIPT_DIR=`realpath $(dirname $0)`
if [[ ! -e $SCRIPT_DIR/../ksy-dl.py ]]; then
    echo "[ - ] Update script must be in the 'tools' directory of the ksy-dl git repository." 1>&2
    exit 1
fi

if [[ -z $KAITAI_FMT_REPO ]]; then
    echo "[ - ] Missing \$KAITAI_FMT_REPO." 1>&2
    exit 1
elif [[ ! -d $KAITAI_FMT_REPO ]]; then
    echo "[ - ] '${KAITAI_FMT_REPO}' does not exist." 1>&2
    exit 1
fi

# check rw permissions
if [[ ! -r $KAITAI_FMT_REPO ]] && [[ ! -w $KAITAI_FMT_REPO ]]; then
    echo "[ - ] '${KAITAI_FMT_REPO}' seems to be inaccessible." 1>&2
    exit 1
fi

echo "[ + ] Updating the git repo...    (${KAITAI_FMT_REPO})"

cd $KAITAI_FMT_REPO
ERROR_PRONE=$(git fetch -q origin master;git merge)
GIT_ECODE=$?

if [[ $? -ne 0 ]]; then
    echo "[ - ] Updating failed. Output of git:" 1>&2
    echo "${ERROR_PRONE}"
    exit $GIT_ECODE
fi

PULL_RESULT=$(echo $ERROR_PRONE | tail -n1)
if [[ "${PULL_RESULT}" == "Already up to date." ]]; then
    echo "[ + ] ${PULL_RESULT}"
    exit 0
fi

DB_FILE=$SCRIPT_DIR/../format-db.json
echo "[ + ] Updating the database...    (${DB_FILE})"

FLIST=$(find . -maxdepth 1 -type d -not -path "*/\.*" | tail -n +2)

PY_OUTPUT=$(python3 -c '
import sys
import json
import os

OMIT_FILES = [
    "_build"
]

def main(flist):
    new_db = {}

    for folder in flist.splitlines():
        if folder in OMIT_FILES:
            continue

        depth = 0
        for parent, _, files in os.walk(folder):
            dname = os.path.basename(parent)

            for file in files:
                if file[-4:] == ".ksy":
                    # remove extension
                    file = file[:-4]

                    if depth > 0 and dname not in file.split("_"):
                        file = "_".join([dname, file])

                    new_db[file] = os.path.basename(folder)
            depth += 1

    # the file write is handled outside of python because bash
    # already has superior file handling
    print(json.dumps(new_db), file = sys.stdout)

main(sys.argv[1])
' "${FLIST}")

if [[ $? -ne 0 ]]; then
    echo "[ - ] Failed to produce the updated DB." 1>&2
    exit 1
fi

echo "${PY_OUTPUT}" > $DB_FILE

if [[ $? -ne 0 ]]; then
    echo "[ - ] Failed to update the DB." 1>&2
    exit 1
fi

echo "[ + ] Done."