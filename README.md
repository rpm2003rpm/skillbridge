# Python-Skill Bridge


Worsened version of skill bridge that works with the setup I have available. I also removed a lot of features so it is easier to tune skillbridge to different requirements.

Modificiations include:

1) Server runs on python-2.7 (I have a old setup running on virtualbox).
2) Comunications use the AF_INET socket trough address 127.0.0.1 and port 52425 by default, but it can be changed.
3) Client on python3 as (In my case, the client is running on the host machine).
4) No cammel to snake translations. What you write is what you got. 
5) Removed function grouping. All functions can be accessed with the underline attribute (including the ones needed to be registered as user functions in the original code). 
6) No division between workspaces. Only one workspace is available.

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
    from skillbridge import Symbol, Workspace, Key
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
