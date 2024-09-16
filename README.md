# Python-Skill Bridge


Simplified version of skillbridge. I removed a lot of features in attempt to get a minimalistic code.

Modificiations include:

1) No cammel to snake translations. What you write is what you get. 
2) Removed function grouping. All functions can be accessed with the underline attribute (including the ones needed to be registered as user functions in the original code). 
3) No division between workspaces. Only one workspace is available.
4) Added the possibility to run raw skill code on the server.
5) Server runs on python-2.7 (I have an old setup running on virtualbox).
6) Comunications use the AF_INET socket trough address 127.0.0.1 and port 52425 by default, but it can be changed.
7) Client runs on python3 (In my case, the client is running on the host machine).

Examples using this version of skillbridge:


1) Show the properties of the cellview opened for edition
```
    from skillbridge import Symbol, Workspace
    ws = Workspace()
    wsf = ws._
    wsf.listFunctions('EditCellView')   #List all the functions that have 'EditCellView' in the name
    p = wsf.geGetEditCellView()         #Get the current cell view
    dir(p)                              #Show the available properties
```

2) Run a dc sweep of the parameter sweep_par from 0 to 1.8, open the results, and plot the voltage in the net /out. 

  
```
    from skillbridge import Symbol, Workspace
    import numpy as np
    import matplotlib.pyplot as plt
    wsf = ws._
    wsg = ws.__   

    wsf.simulator(Symbol("spectre"))
    wsf.design( "libName", "cellName",  "viewName")   #Replace with your lib, cell, and view names
    wsf.resultsDir("~/simulation")
    wsf.path("pathToModels")                          #Replace with the path to your models
    wsf.modelFile(Symbol(("xx.scs",  "")), 
                  Symbol(("xx.scs",  "")), 
                  Symbol(("xx.scs",  "tt")))          #Replace with your models
    wsf.analysis(Symbol("dc"), 
                 param = "sweep_par", 
                 start = "0", 
                 stop = "1.8", 
                 lin = "50" )
    wsf.desVar("sweep_par", 0)
    wsf.save( Symbol("v"), "/out")
    wsf.temp(25)
    wsf.run()  
    
    wsf.openResults("~/simulation/psf")
    data = np.array(wsf.abWaveToList(wsf.getData("/out", result="dc")))
    plt.plot(data[:,0], data[:,1]) 
    plt.grid()
    plt.show()               
```
