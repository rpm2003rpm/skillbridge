# Python-Skill Bridge


Worsened version of skill bridge to work with the setup I have available. I also removed a lot of features so it is easier for me to tune skillbridge to the requirements I need.

Modificiations include:

1) Server runs on virtualbox using python-2.7.
2) Comunications use the AF_INET socket trough address 127.0.0.1 port 52425.
3) Client runs on the host machine using python3.
4) No cammel to snake translations. What you write is what you got. 
5) Removed function grouping. All functions can be accessed with the underline attribute (including the ones needed to be registered as user functions in the original code). 
6) No division between workspaces. Only one workspace is available.

Example:

```
    from skillbridge import Symbol, Workspace
    ws = Workspace.open()
    wsf = ws._
    wsf.listFunctions('EditCellView')   #List all the functions that have 'EditCellView' in the name
    p = wsf.geGetEditCellView()         #Get the current cell view
    dir(p)                              #Show the available properties
```

  

