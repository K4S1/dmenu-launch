#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import argparse
import subprocess
import json
import urllib.parse
import tempfile
import glob
import base64

from collections import namedtuple
from distutils.spawn import find_executable
from datetime import datetime

MenuLauncher = 'dmenu'                      ## Dmenu only support. (I may expand for Rofi support later)
Browser = 'qutebrowser --target window'     ## default browser to use. ex: ## qutebrowser [--target window] ## firefox [--new-window] ## brave ## tor-browser
DefaultSearch = 'dd-DuckDuckGo'             ## web seach default search engien if none is selected
DefaultTheme = 'Default'                    ## Theme of Dmenu possible to add more in the 'get_dmenu_theme' section
ConsoleLaunchCommand = 'konsole -e'         ## Console to launch SSH sessions in. ex: ## alacritty -e  ## kitty  ## konsole -e  ## cool-retro-term -e   
ScriptDir = os.path.dirname(__file__)       ## Folder where script are stored.
RDPSharedFolder = '~/Nextcloud/RDPshare/'   ## shared folder that are connected to RDP

def main():
    args   = get_args()
    scheme = dmenu_setup(args)
    choice = dmenu_call(scheme)
    take_action(scheme, choice)

def check_req_utils(utils):
    for util in utils:
        util = util.split(' ', 1)[0]
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

    if (choise == 'Eyes are not that good'):
        dmenu_theme = theme(
                    font='Droid Sans Mono:Regular:size=16',
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
                          'theme',              # Set dmenu Theme
                          'p',                  # Promt
                          'l',                  # Lines
                         ])

    dmenu = ""
    if args.apps:
        check_req_utils([MenuLauncher, 'exo-open'])
        dmenu = scheme(
                    target='apps',
                    prefix="/usr/share/applications",
                    suffix=".desktop",
                    allownonmatch=False,
                    theme=DefaultTheme,
                    p='APPS',
                    l='0',
                  )
    if args.remmina:
        check_req_utils([MenuLauncher, 'exo-open', 'remmina'])
        dmenu = scheme(
                    target='remmina',
                    prefix=os.path.expanduser('~/.local/share/remmina'),
                    suffix=".remmina",
                    allownonmatch=False,
                    theme=DefaultTheme,
                    p='Remmina',
                    l='0',
                  )
    if args.websearch:
        check_req_utils([MenuLauncher, Browser])
        dmenu = scheme(
                    target='websearch',
                    prefix=ScriptDir + '/websearch',
                    suffix=".txt",
                    allownonmatch=True,
                    theme=DefaultTheme,
                    p='Web Search',
                    l='0',
                  )
    if args.remote:
        check_req_utils([MenuLauncher, Browser, 'bw', 'ssh', 'sshpass', 'ssvncviewer', 'xfreerdp'])
        dmenu = scheme(
                    target='remote',
                    prefix=ScriptDir + '/remote',
                    suffix=".json",
                    allownonmatch=True,
                    theme=DefaultTheme,
                    p='Remote',
                    l='0',
                  )
    
    check_dir_exist(dmenu)
    return dmenu

def dmenu_call(scheme, Prompt=None, CostumChoice=None, NoChoice=False, Password=False):
    choices = []
    if (NoChoice == False and CostumChoice == None):
        for basedir, dirs , files in os.walk(scheme.prefix, followlinks=True):
            dirs.sort()
            files.sort()

            dirsubpath = basedir[len(scheme.prefix):].lstrip('/')
            for f in files:
                if f.endswith(scheme.suffix):
                    full_path = os.path.join(dirsubpath, f.replace(scheme.suffix, '', -1))
                    choices += [full_path]

    if (CostumChoice != None):
        choices = CostumChoice

    theme = get_dmenu_theme(scheme.theme)

    args = ["-fn", theme.font, \
            "-nb", theme.nb,   \
            "-nf", theme.nf,   \
            "-sb", theme.sb,   \
            "-sf", theme.sf,   \
            "-l", scheme.l     ]

    if (Prompt == None):
        args.insert(0, "-p")
        args.insert(1, scheme.p)
    else:
        args.insert(0, "-p")
        args.insert(1, Prompt)

    if Password:
        args.insert(0, "-P")
        
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
        if (CostumChoice != None):
            return choice
        else:
            return (scheme.prefix + "/" + choice + scheme.suffix) 
    else:
        if scheme.allownonmatch or NoChoice:
            return (choice)
        else:
            sys.exit(0)

def take_action(scheme, choice):
    
    if (scheme.target == "apps") or (scheme.target == "remmina"):
        run_subprocess('exo-open "{}"'.format(choice))


    if (scheme.target == "websearch"):
        #print(choice)
        if os.path.isfile(format(choice)):
            #print ("File exist")
            link = open(format(choice), "r").read()
            searchSTR = dmenu_call(scheme, "Search", None, True)
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
            #print(searchFiles)
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
        protocolChoice = []

        if(not os.path.isfile(format(choice))):
            if(format(choice).lower().endswith(' add')):
                #print('add New Host')
                spl_string = choice.split()
                rm = spl_string[:-1]
                choice = ' '.join([str(elem) for elem in rm])
                choice = format(scheme.prefix + "/" + choice + scheme.suffix)
                #print(choice)
                
                #print('Add a protocol to ' + choice)
                #dmenu_call(scheme, Prompt=None, CostumChoice=None, NoChoice=False, Password=False)
                tmpJSON = {}
                tmparr = ['rdp','ssh','web','vnc']
                tmpJSON['protocol'] = dmenu_call(scheme,'Protocol',tmparr).lower()


                if(tmpJSON['protocol'] == 'rdp'):
                    tmpJSON['host'] = dmenu_call(scheme,'Host/IP',None,True)
                    tmpName = dmenu_call(scheme,'Custom Name',None,True)
                    if(tmpName != ''):
                        tmpJSON['name'] = tmpName
                    tmpJSON['authMeth'] = 'pass'
                    templist = bw_list(scheme)
                    BWNameArray = []
                    for i in templist:
                        BWNameArray.append(i['name'])
                    AccountNameChoise = dmenu_call(scheme,'UserID from Bitwarden',BWNameArray)
                    for i in templist:
                        if(i['name'] == AccountNameChoise):
                            tmpJSON['UserID'] = i['id']
                    
                    
                if(tmpJSON['protocol'] == 'ssh'):
                    tmpJSON['host'] = dmenu_call(scheme,'Host/IP',None,True)
                    tmpJSON['port'] = dmenu_call(scheme,'port number',[22])
                    tmpName = dmenu_call(scheme,'Custom Name',None,True)
                    if(tmpName != ''):
                        tmpJSON['name'] = tmpName
                    tmpJSON['authMeth'] = dmenu_call(scheme,'Authentication Method',['key','pass'])
                    templist = bw_list(scheme)
                    BWNameArray = []
                    for i in templist:
                        if(tmpJSON['authMeth'] == 'key'):
                            if('attachments' in i ):
                                BWNameArray.append(i['name'])
                        else:
                            BWNameArray.append(i['name'])
                    AccountNameChoise = dmenu_call(scheme,'UserID from Bitwarden',BWNameArray)
                    for i in templist:
                        if(i['name'] == AccountNameChoise):
                            tmpJSON['UserID'] = i['id']
                            if(tmpJSON['authMeth'] == 'key'):
                                if('attachments' in i ):
                                    if (len(i['attachments']) > 1):
                                        tmpJSON['keyFile'] = dmenu_call(scheme,'UserID from Bitwarden',i['attachments'])
                                    else:
                                        tmpJSON['keyFile'] = i['attachments'][0]

                    tmpJSON['option'] = isSSHcompatibleWithHost(tmpJSON['host'],tmpJSON['port'])
                    
                    
                if(tmpJSON['protocol'] == 'web'):
                    tmpJSON['url'] = dmenu_call(scheme,'URL',None,True)
                    tmpName = dmenu_call(scheme,'Custom Name',None,True)
                    if(tmpName != ''):
                        tmpJSON['name'] = tmpName
                    tmpBrowser = dmenu_call(scheme,'Browser command',None,True)
                    if(tmpBrowser != ''):
                        tmpJSON['browser'] = tmpBrowser
                    

                if(tmpJSON['protocol'] == 'vnc'):
                    tmpJSON['host'] = dmenu_call(scheme,'Host/IP',None,True)
                    tmpName = dmenu_call(scheme,'Custom Name',None,True)
                    if(tmpName != ''):
                        tmpJSON['name'] = tmpName
                    tmpJSON['authMeth'] = 'pass'
                    templist = bw_list(scheme)
                    BWNameArray = []
                    for i in templist:
                        BWNameArray.append(i['name'])
                    AccountNameChoise = dmenu_call(scheme,'UserID from Bitwarden',BWNameArray)
                    for i in templist:
                        if(i['name'] == AccountNameChoise):
                            tmpJSON['UserID'] = i['id']
                    
                if(tmpJSON['protocol'] == 'vnc' and tmpJSON['host'] != '' and tmpJSON['UserID'] != '' or tmpJSON['protocol'] == 'web' and tmpJSON['url'] != '' or tmpJSON['protocol'] == 'ssh' and tmpJSON['host'] != '' and tmpJSON['UserID'] != '' and tmpJSON['authMeth'] != '' or tmpJSON['protocol'] == 'rdp' and tmpJSON['host'] != '' and tmpJSON['UserID'] != '' ): 

                    if(os.path.isfile(choice)):
                        HostJSON = json.loads(open(format(choice), "r").read())
                        HostJSON['protocols'].append(tmpJSON)

                        write_json(HostJSON,format(choice))    
                    else:
                        # Create New File
                        HostJSON = {}
                        HostJSON['protocols'] = [tmpJSON]

                        write_json(HostJSON,format(choice))

            elif(format(choice).lower().endswith(' del')):
                #print('delete existing protocol')
                spl_string = choice.split()
                rm = spl_string[:-1]
                choice = ' '.join([str(elem) for elem in rm])
                choice = format(scheme.prefix + "/" + choice + scheme.suffix)
                #print(choice)
                if(os.path.isfile(choice)):
                    HostJSON = json.loads(open(format(choice), "r").read())
                    choiceArrayNumber = 0
                    if (len(HostJSON['protocols']) > 1):
                        tmparr = []
                        for protocol in HostJSON['protocols']:
                            #print(protocol['protocol'])
                            if "name" in protocol:
                                tmparr.insert(0, protocol['name'])
                            else:
                                tmparr.insert(0, protocol['protocol'])
                        
                        tmparr.append('All')
                        tmp = dmenu_call(scheme,'Protocol',tmparr)

                        tmpcounter = 0
                        if(tmp == 'All'):
                            choiceArrayNumber = -99
                        else:
                            for protocol in HostJSON['protocols']:
                                if "name" in protocol:
                                    if (protocol['name'] == tmp):
                                        protocolChoice = protocol
                                        choiceArrayNumber = tmpcounter
                                else:
                                    if (protocol['protocol'] == tmp):
                                        protocolChoice = protocol
                                        choiceArrayNumber = tmpcounter
                                tmpcounter+=1

                        approval = dmenu_call(scheme,'Are You Sure ?',['No','Yes']).lower()
                        if(approval == 'yes'):
                            if(choiceArrayNumber >= 0):
                                HostJSON['protocols'].pop(choiceArrayNumber)
                                write_json(HostJSON,format(choice))
                            else:
                                os.remove(choice)

                    else:
                        approval = dmenu_call(scheme,'Are You Sure ?',['No','Yes']).lower()
                        if(approval == 'yes'):
                            os.remove(choice)

            elif(format(choice).lower().endswith(' mod')):
                print('modify existing protocol')

            sys.exit(0)

        HostJSON = json.loads(open(format(choice), "r").read())
        choiceArrayNumber = 0
        #print(HostJSON)
        #print(len(HostJSON['protocols']))
        if (len(HostJSON['protocols']) > 1):
            tmparr = []
            for protocol in HostJSON['protocols']:
                #print(protocol['protocol'])
                if "name" in protocol:
                    tmparr.insert(0, protocol['name'])
                else:
                    tmparr.insert(0, protocol['protocol'])
            
            tmp = dmenu_call(scheme,'Protocol',tmparr)

            tmpcounter = 0
            for protocol in HostJSON['protocols']:
                if "name" in protocol:
                    if (protocol['name'] == tmp):
                        protocolChoice = protocol
                        choiceArrayNumber = tmpcounter
                else:
                    if (protocol['protocol'] == tmp):
                        protocolChoice = protocol
                        choiceArrayNumber = tmpcounter
                tmpcounter+=1
        else:
            protocolChoice = HostJSON['protocols'][choiceArrayNumber]

        ####
        # Check protocol
        ####
        if (protocolChoice['protocol'].lower() == "vnc"):
            BWJSON = bw_get_login(scheme,protocolChoice['UserID'])

            cmd = 'ssvncviewer '

            if "option" in protocolChoice:
                cmd = cmd + protocolChoice['option'] + ' '
            
            cmd = cmd + '-scale autofit '
            cmd = cmd + '-passwd <(vncpasswd -f <<<"' + BWJSON['password'] + '") '
            cmd = cmd + protocolChoice['host'] +' '

            run_subprocess(cmd)
            time.sleep(.5)


        if (protocolChoice['protocol'].lower() == "ssh"):
            check_req_utils([ConsoleLaunchCommand.partition(' ')[0]])

            BWJSON = bw_get_login(scheme,protocolChoice['UserID'])
            cmd = 'ssh -o StrictHostKeyChecking=no '

            if "option" in protocolChoice:
                cmd = cmd + protocolChoice['option'] + ' '

            if "port" in protocolChoice:
                cmd = cmd + '-p ' + protocolChoice['port'] + ' '

            if (protocolChoice['authMeth'].lower() == 'key'):
                TempFile = bw_get_attachment(scheme,protocolChoice['UserID'],protocolChoice['keyFile'])
                cmd = cmd + '-i ' + TempFile + ' '

            if (protocolChoice['authMeth'].lower() == 'pass'):
                TempFile = create_tmp_file_mkstemp(BWJSON['password'])
                cmd = 'sshpass -f ' + TempFile + ' ' + cmd
                
            cmd = cmd  + BWJSON['username'] + '@' + protocolChoice['host']
            cmd = ConsoleLaunchCommand + " " + cmd

            #print(cmd)
            run_subprocess(cmd)
            time.sleep(10)

            if (protocolChoice['authMeth'].lower() == 'key' or protocolChoice['authMeth'].lower() == 'pass'):
                os.remove(TempFile)


        if (protocolChoice['protocol'].lower() == "web"):
            if ("browser" in protocolChoice):
                check_req_utils([protocolChoice['browser'].partition(' ')[0]])
                run_subprocess(protocolChoice['browser'] + ' '+ protocolChoice['url'])
            else:
                run_subprocess(Browser + ' '+ protocolChoice['url'])
            time.sleep(.5)


        if (protocolChoice['protocol'].lower() == "rdp"):
            BWJSON = bw_get_login(scheme,protocolChoice['UserID'])

            cmd = 'xfreerdp '
            if ("RDPfile" in protocolChoice):
                cmd = cmd + ScriptDir + '/remote/' + protocolChoice['RDPfile'] + ' '
            #cmd = cmd + '+window-drag '
            #cmd = cmd + '+menu-anims '
            #cmd = cmd + '-themes '
            #cmd = cmd + '-fonts '
            #cmd = cmd + '-wallpaper '
            #cmd = cmd + '/console '
            cmd = cmd + '/bpp:32 '
            #cmd = cmd + '-decorations '
            #cmd = cmd + '-compression '
            cmd = cmd + '/audio-mode:0 '
            cmd = cmd + '/mic:format:1 '
            cmd = cmd + '/sound:latency:50 '
            cmd = cmd + '+auto-reconnect '
            cmd = cmd + '/auto-reconnect-max-retries:4 '
            #cmd = cmd + '/span '         #Span screen over multiple monitors
            #cmd = cmd + '/multimon '
            cmd = cmd + '/drive:RDPshare,' + os.path.expanduser(RDPSharedFolder) + ' '
            #cmd = cmd + '/floatbar '    #[:sticky:[on|off],default:[visible|hidden],show:[always|fullscreen||window]]
            cmd = cmd + '/w:1900 '
            cmd = cmd + '/h:1000 '
            cmd = cmd + '/dynamic-resolution '
            #cmd = cmd + '/f '            # fullscreen
            #cmd = cmd + '/title:Duuuud '
            cmd = cmd + '+clipboard '
            cmd = cmd + '/cert-ignore '
            #cmd = cmd + '-heartbeat '
            if ("SNIdomain" in protocolChoice):
                cmd = cmd + '/u:\'' + BWJSON['username'] + '@' + BWJSON['SNIdomain'] + '\' '
            elif ("domain" in protocolChoice):
                cmd = cmd + '/u:\''+ BWJSON['domain'] + '\\' + BWJSON['username'] + '\' '
            else:
                cmd = cmd + '/u:\'' + BWJSON['username'] + '\' '
            cmd = cmd + '/p:\'' + BWJSON['password'] + '\' '
            if ("RDPfile" not in protocolChoice):
                cmd = cmd + '/v:'+ protocolChoice['host'] + ' '
            
            run_subprocess(cmd)
            time.sleep(.5)

        if("ConnectionTimes" in protocolChoice):
            HostJSON['protocols'][choiceArrayNumber]['ConnectionTimes'] = protocolChoice['ConnectionTimes'] + 1
        else:
            HostJSON['protocols'][choiceArrayNumber]['ConnectionTimes'] = 1

        HostJSON['protocols'][choiceArrayNumber]['LastConnection'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # theTime = datetime.strptime(HostJSON['protocols'][choiceArrayNumber]['LastConnection'], '%Y-%m-%d %H:%M:%S')
        # print(theTime.strftime('Year is %Y, Month is %m, Day is %d, and Time is %H:%M:%S'))

        write_json(HostJSON,format(choice))
            

def run_subprocess(cmd):
    #print(cmd)
    subprocess.Popen(cmd, stdin =subprocess.PIPE,
                          stderr=subprocess.PIPE,
                          stdout=subprocess.PIPE,
                          shell=True,)

def bw_list(scheme):
    
    sessionID = bw_get_session(scheme)
    
    result = subprocess.run(['bw', 'list', 'items', '--session', sessionID], stdout=subprocess.PIPE)
    BWJSON = json.loads(result.stdout)

    JsonReturn = {}
    tempArr = []

    for i in BWJSON:
        if 'login' in i:
            tmpJSON = {}
            tmpJSON['id'] = i['id']
            tmpJSON['name'] = i['name']
            tmpJSON['username'] = i['login']['username']
            if 'attachments' in i:
                tmpJSON['attachments'] = []
                for a in i['attachments']:
                    tmpJSON['attachments'].append(a['fileName'])
            
            tempArr.append(tmpJSON)

    del result
    del BWJSON
    JsonReturn['Users'] = tempArr
    #print(JsonReturn['Users'])
    return(JsonReturn['Users'])

def bw_get_login(scheme,id):
    
    sessionID = bw_get_session(scheme)
    
    result = subprocess.run(['bw', 'get', 'item', id, '--session', sessionID], stdout=subprocess.PIPE)
    BWJSON = json.loads(result.stdout)
    
    JsonReturn = BWJSON['login']

    if 'fields' in BWJSON:
        for costum in BWJSON['fields']:
            JsonReturn[costum['name']] = costum['value']


    del result
    del BWJSON
    #print(JsonReturn)
    return(JsonReturn)

def bw_get_attachment(scheme,id,filename):
    
    sessionID = bw_get_session(scheme)
    
    #print('bw get attachment ' + filename + ' --raw --itemid ' + id + '--session ' + sessionID)
    
    #result = subprocess.run(['bw', 'get', 'attachment', filename, '--raw', '--itemid', id, '--session', sessionID], stdout=subprocess.PIPE)
    #print(result)
    
    command = subprocess.Popen(['bw', 'get', 'attachment', filename, '--raw', '--itemid', id, '--session', sessionID],
                             stdin=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             stdout=subprocess.PIPE)

    stdout_data, errors = command.communicate()
    #print(stdout_data'.decode('utf-8')')

    Path = create_tmp_file_mkstemp(stdout_data.decode('utf-8'))
    del stdout_data
    return(Path)

def bw_get_session(scheme):
    
    txtfiles = []
    tmpfile = ''
    sessionID = ''
    for file in glob.glob('/tmp/kiZIN*'):
        txtfiles.append(file)
        tmpfile = file
        #print(file)


    #if (tmpfile != ''): # ONLY for TESTING GET SESSION
    #    os.remove(tmpfile)
    #    tmpfile = ''

    if (tmpfile == ''): 
        #print('no tmp file get session')

        dmenu = subprocess.Popen(['bw', 'unlock', '--raw'],
                             stdin=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             stdout=subprocess.PIPE)

        sessionID, errors = dmenu.communicate(dmenu_call(scheme, "Unlock Pass", None, True, True).encode('utf-8'))

        #print(sessionID)
        if (sessionID == b''):
            sys.exit(0)
        
        create_tmp_file(sessionID,'kiZIN')

        dmenu = subprocess.Popen(['bw', 'sync', '--session', sessionID],
                             stdin=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             stdout=subprocess.PIPE)

        stdout_data, errors = dmenu.communicate()
        #print(stdout_data)

    else:
        #print('Session found, open session')
        f = open(tmpfile, "r")
        sessionID = f.read()
    
    return sessionID

def create_tmp_file_mkstemp(message):
    fp = tempfile.mkstemp()
    #print('Handle:', fp[0])
    #print('FilePath:', fp[1])
    #print(message)
    try:
        with os.fdopen(fp[0], 'w+') as tmp:
            tmp.write(message)
            tmp.seek(0)
            tmp.close()
            # read temp file
            #s = tmp.read()
            #print(s)
    finally:
        return fp[1]

def create_tmp_file(str,prefix=None,suffix=None,delete=False):
    with tempfile.NamedTemporaryFile(prefix=prefix,suffix=suffix,delete=delete) as t:
        t.write(str)
        path = t.name
        t.close()
        #print(path)
        return path
    
def write_json(data, filename): 
    filenameArr = filename.split('/')
    filename = filenameArr[len(filenameArr) - 1]
    filenameArr.pop(len(filenameArr) - 1)
    path = '/'.join(filenameArr)

    if(not os.path.isdir(path)):
        os.makedirs(path)

    with open(path + '/' + filename,'w') as f: 
        json.dump(data, f, indent=4) 

def isSSHcompatibleWithHost(host,port='22'):
    import socket
    import re
    import xmltodict
    import platform

    NmapResult = subprocess.run(['nmap','--script','ssh2-enum-algos','-sV','-p',port,'-oX','-',host], stdout=subprocess.PIPE)

    NmapArray = str(NmapResult).split("\\n")
    del NmapArray[0:4]
    NmapArray.pop()
    NmapXMLstr = ''.join(NmapArray)

    NMAPJSON = json.loads(json.dumps(xmltodict.parse(NmapXMLstr), indent=4, sort_keys=True))
    #print(NMAPJSON['nmaprun']['host']['ports']['port']['script']['table'])    ## Help digging

    encryption_algorithms = NMAPJSON['nmaprun']['host']['ports']['port']['script']['table'][2]['elem']
    kex_algorithms = NMAPJSON['nmaprun']['host']['ports']['port']['script']['table'][0]['elem']
    mac_algorithms = NMAPJSON['nmaprun']['host']['ports']['port']['script']['table'][3]['elem']


    #ssh -G localhost | grep "ciphers\|kexalgorithms\|macs"
    LocalCiphers = ["chacha20-poly1305@openssh.com","aes128-ctr","aes192-ctr","aes256-ctr","aes128-gcm@openssh.com","aes256-gcm@openssh.com"]
    LocalKex = [ "curve25519-sha256","curve25519-sha256@libssh.org","ecdh-sha2-nistp256","ecdh-sha2-nistp384","ecdh-sha2-nistp521","diffie-hellman-group-exchange-sha256","diffie-hellman-group16-sha512","diffie-hellman-group18-sha512","diffie-hellman-group14-sha256" ]
    LocalMacs = [ "umac-64-etm@openssh.com","umac-128-etm@openssh.com","hmac-sha2-256-etm@openssh.com","hmac-sha2-512-etm@openssh.com","hmac-sha1-etm@openssh.com","umac-64@openssh.com","umac-128@openssh.com","hmac-sha2-256","hmac-sha2-512","hmac-sha1" ]

    if(isinstance(kex_algorithms, str)):
        kex_algorithms = kex_algorithms.split()

    #print(encryption_algorithms)
    #print(kex_algorithms)
    #print(LocalKex)
    #print(mac_algorithms)

    MatchChiper = 0
    for myChiper in LocalCiphers:
        for thereChiper in encryption_algorithms:
            if myChiper == thereChiper:
                MatchChiper = MatchChiper + 1
                #print('myChiper ' + myChiper + ' = thereChiper ' + thereChiper)
    #print(MatchChiper)

    MatchKex = 0
    for myKex in LocalKex:
        for thereKex in kex_algorithms:
            if myKex == thereKex:
                MatchKex = MatchKex + 1
                #print('myKex ' + myKex + ' = thereKex ' + thereKex)
    #print(MatchKex)

    MatchMacs = 0
    for myMacs in LocalMacs:
        for thereMacs in mac_algorithms:
            if myMacs == thereMacs:
                MatchMacs = MatchMacs + 1
                #print('myMacs ' + myMacs + ' = thereMacs ' + thereMacs)
    #print(MatchMacs)


    #echo cipher cipher-auth mac kex key | xargs -n1 SSH -Q
    options = ''

    if(MatchChiper == 0):
        ChiperResult = subprocess.run(['ssh','-Q','cipher'], stdout=subprocess.PIPE)
        ChiperArray = str(ChiperResult).split('\\n')
        #print(ChiperArray)
        ChiperArray[0] = ChiperArray[0][70:]
        ChiperArray.pop()
        #print(ChiperArray)
        ChiperUni = list((set(ChiperArray) | set(LocalCiphers)) - (set(ChiperArray) & set(LocalCiphers)))
        #print(ChiperUni)
        for myChiper in ChiperUni:
            for thereChiper in encryption_algorithms:
                if myChiper == thereChiper:
                    options = options + '-c ' + myChiper  + ' '
                

    if(MatchKex == 0):
        KexResult = subprocess.run(['ssh','-Q','kex'], stdout=subprocess.PIPE)
        KexArray = str(KexResult).split('\\n')
        #print(KexArray)
        KexArray[0] = KexArray[0][67:]
        KexArray.pop()
        #print(KexArray)
        KexUni = list((set(KexArray) | set(LocalKex)) - (set(KexArray) & set(LocalKex)))
        #print(KexUni)
        for myKex in KexUni:
            for thereKex in kex_algorithms:
                if myKex == thereKex:
                    options = options + '-o KexAlgorithms=+' + myKex + ' '
        

    if(MatchMacs == 0):
        MacsResult = subprocess.run(['ssh','-Q','mac'], stdout=subprocess.PIPE)
        MacsArray = str(MacsResult).split('\\n')
        #print(MacsArray)
        MacsArray[0] = MacsArray[0][67:]
        MacsArray.pop()
        #print(MacsArray)
        MacsUni = list((set(MacsArray) | set(LocalMacs)) - (set(MacsArray) & set(LocalMacs)))
        #print(MacsUni)
        for myMacs in MacsUni:
            for thereMacs in mac_algorithms:
                if myMacs == thereKex:
                    print(myMacs) 

    return options



# ------------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
# ------------------------------------------------------------------------------
# EOF
# ------------------------------------------------------------------------------