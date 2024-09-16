; Load the python server script using Inter-Process Comunication
;--------------------------------------------------------------------------------------------------
let((_baseName _logDirectory _unbound) ;Local variables


    ; filename, excutable name and log directory 
    ;----------------------------------------------------------------------------------------------
    _filename     = get_filename(piport)                 ;Get the filename of this skill script
    _filename     = pcreReplace(pcreCompile("^ +| +$") _filename "" 0) ;Removing spaces?
    _baseName     = substring(_filename 1 strlen(_filename)-2)         ;Remove il from the name
    _executable   = strcat("\"" _baseName "py\"")                      ;Add py to the name
    _logDirectory = getShellEnvVar("SKILLBRIDGE_LOG_DIRECTORY") || "."
    _defPort      = getShellEnvVar("SKILLBRIDGE_PORT") || "52425"
    _logName      = lsprintf("%s/skillbridge_skill.log" _logDirectory)
    _unbound      = makeTable("JustForUnbound")[""]


    ; Kill the server
    ; Return: True in case of success or nil otherwise
    ;----------------------------------------------------------------------------------------------
    defun(pyKillServer ()
        if(!pyStartServer.ipc then
            printf("server was not running\n")
            nil
        else
            ipcKillProcess(pyStartServer.ipc)
            pyStartServer.ipc = nil
            t
        )
    )


    ; Kill the server and reload the this script
    ; Return: True
    ;----------------------------------------------------------------------------------------------
    defun(pyReloadScript ()
        printf("killing the old server\n")
        pyKillServer()
        load(_filename)
        t
    )


    ; Show the last "len" lines of the log file content
    ; Inputs: len - Optional number of lines. Default is 20 if not specified.
    ; Return: True
    ; ---------------------------------------------------------------------------------------------
    defun(pyShowLog (@optional (len 20))
        let((fin line (lines declare(lines[len])) (ptr 0))
            fin = infile(_logName)
	
            ;Read all the lines in the log file and store then in a circular buffer of length len.
            while(gets(line fin)
                lines[ptr] = line
                ptr = mod(ptr + 1 len)
            )

            ;Read all the lines in the circular buffer from where it stopped.
            for(i 0 len-1
		        line = lines[mod(ptr + i len)]
		        if(boundp(`line) then ;Does it have a valid value, then print.
                    printf("%s" line)
		        )
            )
            printf("")

        )
        t
    )


    ; It seems to encapsulates the calling parameters and return the warnings
    ;---------------------------------------------------------------------------------------------- 
    defmacro(__pyCaptureWarnings (@rest body) ;@rest let you pass an arbitrary number of parameters.
        `let(((tempPort outstring()))         ;Create an out string that can be dumped later.
            unwindProtect(                    ;Similar to finally in java or python. Capture 
                                              ;uncaptured exceptions.
                {
                    let(((woport tempPort))   ;Change the output port to tempPort variable?
                        ,@body                ;The parameters of of _pyCaptureWarnings

                        ; next two lines are to force final 
                        ; warning to be flushed
                        warn("")
                        getWarn()
                    )
                    getOutstring(tempPort)    ;Set the result to the value of the out string
                }
                close(tempPort)
            )
        )
    )


    ; Process received data. 
    ; This function evaluates skill expression in the form of a string
    ; encapsulating the errors in the errset. Error and warnings are captured
    ; and then processed before being sent to the python script. If no errors
    ; are found the result is converted to python (__pySkillToPython) and then
    ; are sent back to the python script.
    ; Inputs: id - id
    ;         data - data from python script
    ; 
    ;----------------------------------------------------------------------------------------------
    defun(__pyOnData (id data)
        foreach(line parseString(data "\n")
            let((result capturedWarning pythonCode)
                capturedWarning = __pyCaptureWarnings(errset(result=evalstring(line)))
                if((errset.errset) then
                    printf("command %L resulted in error %L\n" line errset.errset)
                    ipcWriteProcess(id lsprintf("failure %L\n" errset.errset))
                else
                    if(boundp('result) then
                        pythonCode = __pySkillToPython(result)
                        if((capturedWarning != "" && 
                            capturedWarning != "*WARNING* ") then
                            pythonCode = lsprintf("warning(%L, %s)" 
                                                  capturedWarning 
                                                  pythonCode)
                        )
                        ipcWriteProcess(id lsprintf("success %s\n" pythonCode))
                    else
                        ipcWriteProcess(id "success error('unbound')\n")
                    )
                )
            )
        )
    )


    ; IPC error
    ;----------------------------------------------------------------------------------------------
    defun(__pyOnError (_ data)
        fprintf(stderr "PYTHON: %s\n" data)
    )


    ; IPC finish
    ;----------------------------------------------------------------------------------------------
    defun(__pyOnFinish (_ data)
        printf("server was stopped with code %L\n" data)
        pyStartServer.ipc = nil
    )


    ; Convert a property skill list to a python dictionary string
    ;----------------------------------------------------------------------------------------------
    defun(__pyPropertyListToPython (propList)
        strcat("{"
            buildString(
                mapcar(lambda((key)
                    lsprintf("'%s':%s" key __pySkillToPython(get(propList key))))
                    propList->?)
            ",")
            "}"
        )
    )


    ; Convert a skill list to a python list string
    ;----------------------------------------------------------------------------------------------
    defun(__pyListToPython (thing)
        strcat(
            "["
            buildString(mapcar('__pySkillToPython thing) ",")
            "]"
        )
    )


    ; Convert a skill vector to a python vector calling string
    ;----------------------------------------------------------------------------------------------
    defun(__pyVectorToPython (collection)
        let((symbol)
            symbol = gensym("__py_vector_") ;Creting symbol strating with __py_vector_
            set(symbol collection)
            lsprintf("Vector(%L)" symbolToString(symbol)) ;Return name of the symbol
        )
    )


    ; Convert a skill vector to a python table calling string
    ;----------------------------------------------------------------------------------------------
    defun(__pyTableToPython (collection)
        let((symbol)
            symbol = gensym("__py_table_") ;Creting symbol strating with __py_vector_
            set(symbol collection)
            lsprintf("Table(%L)" symbolToString(symbol)) ;Return name of the symbol
        )
    )

    defun(__pySaveToVariableAndReturn (thing)
        let((repr variableName split objectType address variableSymbol)
            repr = lsprintf("%L" thing)
            if(rexExecute(repr) then
                split = buildString(parseString(repr "_") "")
                split = parseString(split "@:")
                objectType = car(split)
                address = cadr(split)
                variableName = lsprintf("__py_%s_%s" objectType address)
                set(stringToSymbol(variableName) thing)
                lsprintf("Remote(%L)" variableName)
            else if(otherp(thing) then
                variableSymbol = gensym("__py_OTHER_")
                set(variableSymbol thing)
                lsprintf("Remote(%L)" symbolToString(variableSymbol))
            else if(portp(thing) then
                variableSymbol = gensym("__py_openfile_")
                set(variableSymbol thing)
                lsprintf("Remote(%L)" symbolToString(variableSymbol))
            else
                lsprintf("error(%L)" repr)
                printf("I COULD NOT PARSE %L\n" repr)
            )))
        )
    )


    defun(__pySkillToPython (thing)
        if(thing == t then "True" else
        if(!thing then "None" else
        if(or(numberp(thing) stringp(thing)) then lsprintf("%L" thing) else
        if(symbolp(thing) then lsprintf("Symbol('%s')" thing) else
        if(listp(thing) then
            if(and(!car(thing) symbolp(cadr(thing)) cadr(thing) != t)
            then __pyPropertyListToPython(thing)
            else __pyListToPython(thing)
            )
        else
        if(tablep(thing) then __pyTableToPython(thing) else
        if(vectorp(thing) then __pyVectorToPython(thing) else
        rexCompile("^[_a-zA-Z]+[:@][x0-9a-fA-F]+$")
        __pySaveToVariableAndReturn(thing)
        )))))))
    )



    ;Start python server
    ;----------------------------------------------------------------------------------------------
    defun(pyStartServer (@key (address lsprintf("%s,%s" "0.0.0.0" _defPort)) 
                              (logLevel "INFO") 
                              (timeout nil) 
                              (python "python"))
        ; Server is already running
        ;------------------------------------------------------------------------------------------
        if(pyStartServer.ipc then
            fprintf(stderr, "server is already running\n")
            nil
        ; Start server
        ;------------------------------------------------------------------------------------------
        else
            let(((executableWithArgs lsprintf("%s %s %s" 
                                              _executable 
                                              address
                                              logLevel)))
                if(timeout then
                    executableWithArgs = lsprintf("%s --timeout %L" 
                                                  executableWithArgs 
                                                  timeout)
                )
                executableWithArgs = lsprintf("\"%s\" %s" 
                                              python 
                                              executableWithArgs)
                pyStartServer.ipc = ipcBeginProcess(executableWithArgs 
                                                    "" 
                                                    '__pyOnData 
                                                    '__pyOnError 
                                                    '__pyOnFinish 
                                                    _logName)
                t
            )
        )
    )

    pyStartServer.ipc = nil
    _executable
    printf("Available commands:\n")
    printf(lsprintf("%s %s %s" "\tpyStartServer ?address \"0.0.0.0," _defPort "\" ?logLevel \"INFO\" "))
    printf("?timeout nil ?python \"python\"\n")
    printf("\tpyKillServer\n")
    printf("\tpyReloadScript\n")
    printf("\tpyShowLog [numberOfLines]\n")
)

;--------------------------------------------------------------------------------------------------
; Wave object to list
;--------------------------------------------------------------------------------------------------
(procedure (abWaveToList wave @key transpose)
    (let (xList yList xyList len
        (xVec (drGetWaveformXVec wave))
        (yVec (drGetWaveformYVec wave))
    )
        (setq len (drVectorLength xVec))
        (if transpose
            (progn
                (for i 0 (sub1 len)
                    (setq xList (tconc xList (drGetElem xVec i)))
                    (setq yList (tconc yList (drGetElem yVec i)))
                )
                (list (car xList) (car yList))
            )
        ; else
            (progn
                (for i 0 (sub1 len)
                    (setq xyList (tconc xyList (list (drGetElem xVec i)
                    (drGetElem yVec i))))
                )
                (car xyList)
            )
    ) ; if
    ) ; let
) ; procedure

