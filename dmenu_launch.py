#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""\
Simple dmenu launcher for passwords, docs, notes and application shortcuts.

Requirements
---------------
  - dmenu, gpg, pass, xclip, exo-open, pkill

Usage
---------------
  $ dmenu_launch.py [-h] [--pass | --apps | --notes]

Arguments
---------------
  -h, --help  show this help message and exit
  --pass      Chooses a password from password store.
  --apps      Quick launches a desktop application with exo-open.
  --notes     Opens a text/markdown note from a given directory with exo-open.
  --search    Quick search and launch from a given directory with exo-open.

"""
import os
import sys
import argparse
import subprocess
import json
import urllib.parse
import tempfile
import glob

from collections import namedtuple
from distutils.spawn import find_executable

MenuLauncher = 'dmenu' 
Browser = 'qutebrowser'
DefaultSearch = 'dd-DuckDuckGo'


def main():
    check_req_utils()

    args   = get_args()
    scheme = dmenu_setup(args)
    choice = dmenu_input(scheme)
    take_action(scheme, choice)

def check_req_utils():
    """Checks if dmenu and other mandatory utilities can be found on target machine."""
    utils = ([MenuLauncher, 'exo-open', 'pkill', 'remmina', Browser, 'bw'])
    for util in utils:
        if find_executable(util) is None:
            print("ERROR: Util '{}' is missing, install it before proceeding! Exiting!".format(util))
            sys.exit(0)

def check_dir_exist(scheme):
    """Checks required directories are present."""
    if os.path.exists(scheme.prefix) is False:
        print("ERROR: Required directory '{}' is missing! Exiting!").format(scheme.prefix)
        sys.exit(0)

def get_args():
    """Return arguments from stdin or print usage instructions."""
    parser = argparse.ArgumentParser(description='Simple dmenu launcher for passwords, notes and application shortcuts.')
    group = parser.add_mutually_exclusive_group()


    group.add_argument('-a', '--apps', action='store_true',
                        help='Quick launches a desktop application with exo-open.')
    group.add_argument('--remmina', action='store_true',
                        help='Quick Remmina launcher')
    group.add_argument('-w', '--websearch', action='store_true',
                        help='Quick Web Search launcher')
    group.add_argument('-r', '--remote', action='store_true',
                        help='YA remmina attampt replacement')

    if not len(sys.argv) > 1:
        parser.print_help()
        sys.exit(0)

    return parser.parse_args()

def get_dmenu_theme(choise='Default'):
    theme = namedtuple(
                        'dmenu_theme',
                         [
                          'font',               # dmenu font name and size
                          'nb','nf','sb','sf',  # dmenu color:
                                                #   n=normal / s=selected,
                                                #   b=background, f=foreground
                         ])

    dmenu_theme = ""
    if (choise == 'Default'):
        dmenu_theme = theme(
                    font='Droid Sans Mono:Regular:size=10',
                    nb='#222222', nf='#EEEEEE', sb='#005577', sf='#EEEEEE',
                  )
    return dmenu_theme

def dmenu_setup(args):
    """Setup dmenu font, color and size based on user's input."""
    scheme = namedtuple(
                        'dmenu',
                         [
                          'target',             # pass / apps/ notes / search
                          'prefix',             # location prefix (base dir)
                          'suffix',             # file extension to look for
                          'allownonmatch',      # Allow return non matich items in dmenu [True/False]
                          'font',               # dmenu font name and size
                          'nb','nf','sb','sf',  # dmenu color:
                                                #   n=normal / s=selected,
                                                #   b=background, f=foreground
                          'p',                  # Promt
                          'l',                  # Lines

                         ])

    dmenu = ""
    if args.apps:
        dmenu = scheme(
                    target='apps',
                    prefix="/usr/share/applications",
                    suffix=".desktop",
                    allownonmatch=False,
                    font='Droid Sans Mono:Regular:size=10',
                    nb='#222222', nf='#EEEEEE', sb='#005577', sf='#EEEEEE',
                    p='APPS',
                    l='0',
                  )
    if args.remmina:
        dmenu = scheme(
                    target='remmina',
                    prefix=os.path.expanduser('~/.local/share/remmina'),
                    suffix=".remmina",
                    allownonmatch=False,
                    font='Droid Sans Mono:Regular:size=10',
                    nb='#222222', nf='#EEEEEE', sb='#005577', sf='#EEEEEE',
                    p='Remmina',
                    l='0',
                  )
    if args.websearch:
        dmenu = scheme(
                    target='websearch',
                    prefix=os.path.expanduser('~/Nextcloud/Code/PythonScript/dmenu/websearch'),
                    suffix=".txt",
                    allownonmatch=True,
                    font='Droid Sans Mono:Regular:size=10',
                    nb='#222222', nf='#EEEEEE', sb='#005577', sf='#EEEEEE',
                    p='Web Search',
                    l='0',
                  )
    if args.remote:
        dmenu = scheme(
                    target='remote',
                    prefix=os.path.expanduser('~/Nextcloud/Code/PythonScript/dmenu/remote'),
                    suffix=".json",
                    allownonmatch=False,
                    font='Droid Sans Mono:Regular:size=10',
                    nb='#222222', nf='#EEEEEE', sb='#005577', sf='#EEEEEE',
                    p='Remote',
                    l='0',
                  )
    
    check_dir_exist(dmenu)
    return dmenu

def dmenu_input_blank(scheme, Prompt, Password=False):
    args = ["-fn", scheme.font, \
            "-nb", scheme.nb, \
            "-nf", scheme.nf, \
            "-sb", scheme.sb, \
            "-sf", scheme.sf, \
            "-p", Prompt,   \
            "-l", scheme.l    ]
    
    if Password:
        args.insert(0, "-P")
    
    if MenuLauncher == "rofi":
        args.insert(0, "-dmenu")

    dmenu = subprocess.Popen([MenuLauncher] + args,
                             stdin=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             stdout=subprocess.PIPE)

    choice, errors = dmenu.communicate()

    if dmenu.returncode not in [0, 1] \
       or (dmenu.returncode == 1 and len(errors) != 0):
        print("'{} {}' returned {} and error:\n{}"
              .format([MenuLauncher], ' '.join(args), dmenu.returncode,
                      errors.decode('utf-8')))
        sys.exit(0)

    choice = choice.decode('utf-8').rstrip()

    
    if scheme.allownonmatch or Password:
        return (choice)
    else:
        sys.exit(0)


def dmenu_input(scheme):
    """Builds dmenu list of options and returns the value selected by user."""
    choices = []
    for basedir, dirs , files in os.walk(scheme.prefix, followlinks=True):
        dirs.sort()
        files.sort()

        dirsubpath = basedir[len(scheme.prefix):].lstrip('/')
        for f in files:
            if f.endswith(scheme.suffix):
                full_path = os.path.join(dirsubpath, f.replace(scheme.suffix, '', -1))
                choices += [full_path]

    args = ["-fn", scheme.font, \
            "-nb", scheme.nb, \
            "-nf", scheme.nf, \
            "-sb", scheme.sb, \
            "-sf", scheme.sf, \
            "-p", scheme.p,   \
            "-l", scheme.l    ]
    
    if MenuLauncher == "rofi":
        args.insert(0, "-dmenu")

    dmenu = subprocess.Popen([MenuLauncher] + args,
                             stdin=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             stdout=subprocess.PIPE)

    choice_lines = '\n'.join(map(str, choices))
    choice, errors = dmenu.communicate(choice_lines.encode('utf-8'))

    if dmenu.returncode not in [0, 1] \
       or (dmenu.returncode == 1 and len(errors) != 0):
        print("'{} {}' returned {} and error:\n{}"
              .format([MenuLauncher], ' '.join(args), dmenu.returncode,
                      errors.decode('utf-8')))
        sys.exit(0)

    choice = choice.decode('utf-8').rstrip()

    if choice in choices:
        return (scheme.prefix + "/" + choice + scheme.suffix) 
    else:
        if scheme.allownonmatch:
            return (choice)
        else:
            sys.exit(0)

def take_action(scheme, choice):
    
    if (scheme.target == "apps") or (scheme.target == "remmina"):
        run_subprocess('exo-open "{}"'.format(choice))


    if (scheme.target == "websearch"):
        if os.path.isfile(format(choice)):
            link = open(format(choice), "r").read()
            searchSTR = dmenu_input_blank(scheme, "Search")
            if searchSTR:
                link = link.replace("[SEARCH]", urllib.parse.quote(searchSTR))
                run_subprocess(Browser + ' "{}"'.format(link))
            else:
                sys.exit(0)
        else:
            searchFiles = []
            for basedir, dir , files in os.walk(scheme.prefix, followlinks=True):

                dirsubpath = basedir[len(scheme.prefix):].lstrip('/')
                for f in files:
                    if f.endswith(scheme.suffix):
                        full_path = os.path.join(dirsubpath, f.replace(scheme.suffix, '', -1))
                        searchFiles += [full_path]
            for searchFile in searchFiles:
                if searchFile.split('-', 1)[0] == choice.split(' ', 1)[0]:
                    link = open(format(scheme.prefix + "/" + searchFile + scheme.suffix), "r").read()
                    if choice.split(' ', 1)[1]:
                        link = link.replace("[SEARCH]", urllib.parse.quote(choice.split(' ', 1)[1]))
                        run_subprocess(Browser + ' "{}"'.format(link))
                        sys.exit(0)
                    else:
                        sys.exit(0)

            if choice:
                link = open(format(scheme.prefix + "/" + DefaultSearch + scheme.suffix), "r").read()
                link = link.replace("[SEARCH]", urllib.parse.quote(choice))
                run_subprocess(Browser + ' "{}"'.format(link))
                sys.exit(0)
            else:
                sys.exit(0)

    if (scheme.target == "remote"):
        HostJSON = json.loads(open(format(choice), "r").read())
        BWJSON = bw_get_info(scheme,HostJSON['UserID'])
        run_subprocess('ssvncviewer -scale autofit -passwd <(vncpasswd -f <<<"' + BWJSON['password'] + '") '+ HostJSON['host'] +' ')

def run_subprocess(cmd):
    """Handler for shortening subprocess execution."""
    subprocess.Popen(cmd, stdin =subprocess.PIPE,
                          stderr=subprocess.PIPE,
                          stdout=subprocess.PIPE,
                          shell=True,)

def bw_get_info(scheme,id):
    
    sessionID = bw_get_session(scheme)
    
    try: 
        result = subprocess.run(['bw', 'get', 'item', id, '--session', sessionID], stdout=subprocess.PIPE)
    except: 
        print(':\')')

    try: 
        BWJSON = json.loads(result.stdout)
    except: 
        print(':\') 2')

    return(BWJSON['login'])

def bw_get_session(scheme):
    
    txtfiles = []
    tmpfile = ''
    sessionID = ''
    for file in glob.glob('/tmp/kiZIN*'):
        txtfiles.append(file)
        tmpfile = file

    #if (tmpfile != ''): # ONLY for TESTING GET SESSION
    #    os.remove(tmpfile)
    #    tmpfile = ''

    if (tmpfile == ''): 

        dmenu = subprocess.Popen(['bw', 'unlock', '--raw'],
                             stdin=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             stdout=subprocess.PIPE)

        sessionID, errors = dmenu.communicate(dmenu_input_blank(scheme, "Unlock Pass",True).encode('utf-8'))

        if (sessionID == b''):
            sys.exit(0)
        
        create_tmp_file(sessionID,'kiZIN')

        dmenu = subprocess.Popen(['bw', 'sync', '--session', sessionID],
                             stdin=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             stdout=subprocess.PIPE)

        stdout_data, errors = dmenu.communicate()

    else:
        f = open(tmpfile, "r")
        sessionID = f.read()
    
    return sessionID

def create_tmp_file(str,prefix=None,suffix=None,delete=False):
    with tempfile.NamedTemporaryFile(prefix=prefix,suffix=suffix,delete=delete) as t:
        t.write(str)
        path = t.name
        t.close()
        return path
    
    


# ------------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
# ------------------------------------------------------------------------------
# EOF
# ------------------------------------------------------------------------------