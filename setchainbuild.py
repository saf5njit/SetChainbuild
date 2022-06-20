# Author: Santiago A. Flores Roman
# Describption: Edition of the file Usf-potential.py, created by Dr. Gor to simulate on Chainbuild.
# Requirements: Python3.
# Instructions: 
#   Run the following command: python3 UsfPotential.py [File of Potentials] [File of Input Parameters]
#   The script will create the .sol, .inp, and .mol files, as well as an sbatch file 
#   (and a bash file) that will run several points according to the File of Input Parameters.
#   To run Chainbuild, its excecutable (chainbuild) must be on the same path of the rest of the input files
#   (mol, sol, and inp).
# 
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

import numpy as np
import re,sys,os,shutil
import scipy.constants as const

planck = const.Planck #J*s
kb = const.Boltzmann #J/K
avogadro = const.Avogadro #mol^-1

class System():
    def __init__(self,argv):
        self.programParameters = {}
        self.stateVariables = {}
        self.poreParameters = {}
        self.fluidParameters = {}
        self.scriptParameters = {}
        self.scriptParameters['inputfile'] = argv[1]
        self.scriptParameters['scriptname'] = argv[0]

    def Help(self):
        scriptName = self.scriptParameters['scriptname']
        print('You called Help.\n'
              'Description: This script creates the files to run a simulation on chainbuild.\n'
              'Requirements: Numpy and Scipy.\n'
              'Instructions:\n'
              f'\tExecute: python3 {scriptName} [input file]\n'
              '\n'
              '\tParameters:\n'
              '\t\t# Simulation Parameters:\n'
              '\t\t\tEquilibrationSets [value]\n'
              '\t\t\tProductionSets [value]\n'
              '\t\t\tStepsPerSet [value]\n'
              '\t\t\tPrintEveryNSets [value]\n'
              '\t\t\tEnsemble [nvt|gce]\n'
              '\t\t# State Variables:\n'
              '\t\t\tExternalTemperature [value] (in K)\n'
              '\t\t\tExternalPressure [list of values separated by spaces] (in Pa)\n'
              '\t\t\tNumberOfMolecules [list of values separated by spaces]\n'
              '\t\t\tFugacityCoefficient [value or list of values separated by spaces]\n'
              '\t\t# Fluid-Fluid Interaction Parameters:\n'
              '\t\t\tMoleculeName [name]\n'
              '\t\t\tSigma_ff [value] (in nm)\n'
              '\t\t\tsigma2_ff [value] (in nm). Only for SquareWell potential\n'
              '\t\t\trcut_ff [value] (in nm)\n'
              '\t\t\tEpsilon_ff [value] (in nm)\n'
              '\t\t\tMolarMass [value] (in g/mol)\n'
              '\t\t\tU_ff [lj|SquareWell]\n'
              '\t\t# Solid-Fluid Interaction Parameters:\n'
              '\t\t\tGeometry [number] [name]\n'
              '\t\t\tPoreSize [list of values separated by spaces]\n'
              '\t\t\tN_s [value] (in nm^-2)\n'
              '\t\t\tEpsilon_sf [value] (in K)\n'
              '\t\t\tSigma_sf [value] (in K)\n'
              '\t\t\tSigma2_sf [value] (in nm)\n'
              '\t\t\tRcut_sf [value] (in nm)\n'
              '\t\t# Files containing the potentials:\n'
              '\t\t\tUsfFile [file name] (python script). Include the extension, and use only lower case for the file name.\n'
              '\t\t\tPhiFile [file name] (python script). Include the extension, and use only lower case for the file name.\n'
              '\t\t\tMuFile [file name] (python script). Include the extension, and use only lower case for the file name.\n'
              '\t\t# Bash Parameters:\n'
              '\t\t\tStdOut [file name]\n'
              '\t\t\tStdErr [file name]\n'
              '\t\t\tRunSbatch [Yes|No]\n'
              '\t\t\t\tNumberOfProcessors [value]. Only if RunSbatch is set to No\n'
              '\t\t\t\tEmail [email address]\n'
              '\t\t\t\tEmailType [none|begin|end|fail|requeue|all]\n'
              '\t\t\t\tJobName [name]\n'
              '\n'
              'Notes:\n'
              '\t1.-  The input file contains the parameters to set the simulations.\n'
              '\t2.-  Valid pairs of geometries:\n'
              '\t     \t1 Spherical. For U=U(r)\n'
              '\t     \t2 Spherical. For U=U(r,theta)\n'
              '\t     \t3 Bulk. With PBC, doesn\'t need a U_sf file\n'
              '\t     \t3 Space. Without PBC, doesn\'t need a U_sf file\n'
              '\t     \t3 Box. With inf potentials as walls, doesn\'t need a U_sf file\n'
              '\t     \t3 Slit. For U=U(x,y,z)\n'
              '\t     \t5 Cylindrical. For U=U(z,rho)\n'
              '\t     \t6 Cylindrical. For U=U(r)\n'
              '\t3.-  The U_sf file must contain a function called Usf=Usf(x,params),\n'
              '\t     where x is a numpy vector of positions: r, (r,theta), (x,y,z), (r,rho). Also rcut could be sigma2 (depending \n'
              '\t     on the potential), and params is a dictionary with all the fluid-fluid and solid-fluid parameters given by the user.\n'
              '\t     This file doesn\'t need to be created if Geometry specifies bulk, space or box in its second argument.\n'
              '\t     Example of a calling to a parameter in the dictionary: epsilon_ff = param[\'epsilon_ff[K]\']. Also you can see the'
              '\t     whole dictionary by printing it.\n'
              '\t4.-  The Phi file must contain a function called Phi=Phi(P,params), where P is a numpy array of pressures.\n'
              '\t     This file doesn\'t need to be created if fugacityCoefficient or a mu file is given. In that case, the program\n'
              '\t     itself will calculate the chemical potentials.\n'
              '\t5.-  The Mu file must contain a function called Mu=Mu(P,params), where P is a numpy array of pressures.\n'
              '\t     This file doesn\'t need to be created if FugacityCoefficient or a phi file is given. In that case, the program\n'
              '\t     itself will calculate the chemical potentials.\n'
              '\t6.-  Chainbuild also calculates chemical potentials by using Widom Insertion. It\'s automatically activated when \n'
              '\t     defining the NVT ensemble.\n'
              '\t7.-  You cannot define sigma2 and rcut at the same time (either for fluid-fluid or solid-fluid interactions).\n'
              '\t8.-  The quantities expressed in reduced units are quantities divided by epsilon_ff[K] or sigma_ff[nm]\n'
              '\t9.-  The parameters Email, EmailType and JobName don\'t need to be defined if RunSbatch is set to No or is not defined.\n'
              '\t10.- For any comment in the input file, use #.\n')
        sys.exit(0)

    def ReadFileOfInputParameters(self):
        inputFileName = self.scriptParameters['inputfile']
        with open(inputFileName,'r') as fileContent: fileLines = fileContent.readlines()
        for line in range(len(fileLines)):
            params = re.search(r'^\s*([a-z\d_]+)\s+?([\d\.a-z@\s]+)',fileLines[line],flags=re.IGNORECASE)
            if params:
                command = params.group(1).lower()
                value = params.group(2).lower()[:-1]
                # Program parameters
                if command == 'equilibrationsets': self.programParameters[command] = int(value)
                elif command == 'productionsets': self.programParameters[command] = int(value)
                elif command == 'stepsperset': self.programParameters[command] = int(value)
                elif command == 'printeverynsets': self.programParameters[command] = int(value)
                elif command == 'ensemble': self.programParameters[command] = value #gce, nvt
                # State variables
                elif command == 'externalpressure': 
                    self.stateVariables[command+'[Pa]'] = np.array(list(map(float,value.split()))) #For several pressures. Pa
                elif command == 'numberofmolecules': 
                    self.stateVariables[command] = np.array(list(map(int,value.split()))) #For several numbers of molecules.
                elif command == 'externaltemperature': self.stateVariables[command+'[K]'] = float(value)
                elif command == 'fugacitycoefficient': self.stateVariables[command] = np.array(list(map(float,params.group(2).split()))) # For several values 
                # Fluid-Fluid parameters
                elif command == 'moleculename': self.fluidParameters[command] = value #Arbitrary
                elif command == 'sigma_ff': self.fluidParameters[command+'[nm]'] = float(value) #nm
                elif command == 'sigma2_ff': self.fluidParameters[command+'[nm]'] = float(value) #nm
                elif command == 'rcut_ff': self.fluidParameters[command+'[nm]'] = float(value) #nm
                elif command == 'epsilon_ff': self.fluidParameters[command+'[K]'] = float(value) #K
                elif command == 'molarmass': self.fluidParameters[command+'[g/mol]'] = float(value) #g/mol
                elif command == 'u_ff': self.fluidParameters[command] = value #LennardJones, SquareWell
                # Pore parameters
                elif command == 'poresize': 
                    self.poreParameters[command+'[nm]'] = np.array(list(map(float,params.group(2).split()))) #For several pore sizes. nm
                elif command == 'n_s': self.poreParameters[command+'[nm^-2]'] = float(value) #nm^-2
                elif command == 'epsilon_sf': self.poreParameters[command+'[K]'] = float(value) #K
                elif command == 'sigma_sf': self.poreParameters[command+'[nm]'] = float(value) #nm
                elif command == 'sigma2_sf': self.poreParameters[command+'[nm]'] = float(value) #nm
                elif command == 'rcut_sf': self.poreParameters[command+'[nm]'] = float(value) #nm
                elif command == 'geometry': 
                    self.poreParameters[command] = value.split()
                    self.poreParameters[command][0] = int(self.poreParameters[command][0])
                # Files to read
                elif command == 'usffile': self.scriptParameters[command] = value #K
                elif command == 'mufile': self.scriptParameters[command] = value #K
                elif command == 'phifile': self.scriptParameters[command] = value
                # Sbatch
                elif command == 'runsbatch': self.scriptParameters[command] = value
                elif command == 'numberofprocessors': self.scriptParameters[command] = int(value)
                elif command == 'email': self.scriptParameters[command] = value
                elif command == 'emailtype': self.scriptParameters[command] = value
                elif command == 'stdout': self.scriptParameters[command] = value
                elif command == 'stderr': self.scriptParameters[command] = value
                elif command == 'jobname': self.scriptParameters[command] = value
        # Reducing parameters and variables.
        self.stateVariables['externaltemperature'] = self.stateVariables['externaltemperature[K]']/self.fluidParameters['epsilon_ff[K]']
        self.poreParameters['poresize'] = self.poreParameters['poresize[nm]']/self.fluidParameters['sigma_ff[nm]']
        if 'rcut_ff[nm]' in self.fluidParameters.keys():
            self.fluidParameters['rcut_ff'] = self.fluidParameters['rcut_ff[nm]']/self.fluidParameters['sigma_ff[nm]']
        if 'rcut_sf[nm]' in self.fluidParameters.keys():
            self.poreParameters['rcut_sf'] = self.poreParameters['rcut_sf[nm]']/self.fluidParameters['sigma_ff[nm]']

    def CheckErrors(self):
        # simulation sets and steps.
        if (('equilibrationsets' not in self.programParameters.keys())\
            or ('productionsets' not in self.programParameters.keys())\
            or ('stepsperset' not in self.programParameters.keys())\
            or ('printeverynsets' not in self.programParameters.keys())):
            raise KeyError('Simulation steps or sets weren\'t defined.')
        # state variables.
        if 'fugacitycoefficient' in self.stateVariables.keys():
            pressures = self.stateVariables['externalpressure[Pa]']
            phi = self.stateVariables['fugacitycoefficient']
            if (len(phi) != len(pressures)) and (len(phi) != 1): 
                raise ValueError('List of fugacity coefficients must be of the same length as pressures or only of one value.\n'
                                 f'Number of fugacity coefficients: {len(phi)}; Number of pressures: {len(pressures)}.')
        if 'externaltemperature' not in self.stateVariables.keys(): raise KeyError('ExternalTemperature was not defined.')
        # ensemble.
        if ('ensemble' not in self.programParameters.keys()):
            raise KeyError('Ensemble was not defined: nvt or gce.')
        ensemble = self.programParameters['ensemble']
        if (ensemble != 'gce' and ensemble != 'nvt'): 
            raise NameError(f'Wrong ensemble. Only two are accepted: gce (Grand Canonical ensemble) and nvt (Canonical ensemble). '
                            f'Ensemble given: {ensemble}')
        # Fluid-Fluid and Solid-Fluid parameters.
        # rcut and sigma2.
        if (('rcut_ff' in self.fluidParameters.keys() and 'sigma2_ff' in self.fluidParameters.keys())\
            or ('rcut_sf' in self.poreParameters.keys() and 'sigma2_sf' in self.poreParams.keys())):
            raise KeyError('You must define one either rcut or sigma2, depending on the potential.')
        # sigma_ff and epsilon_ff
        if 'sigma_ff[nm]' not in self.fluidParameters.keys(): raise KeyError('sigma_ff was not defined.')
        if 'epsilon_ff[K]' not in self.fluidParameters.keys(): raise KeyError('epsilon_ff was not defined.')
        # molar mass
        if 'molarmass[g/mol]' not in self.fluidParameters.keys(): raise KeyError('molar mass was not defined.')
        # U_ff
        if 'u_ff' not in self.fluidParameters.keys(): raise KeyError('Intermolecular potential was not defined.')
        uff = self.fluidParameters['u_ff']
        if uff != 'squarewell' and uff != 'lj': 
            raise NameError('Wrong intermolecular potential. Valid potentials: LJ (Lennard Jones) and SquareWell. '
                            f'Potential given: {uff}')
        # geometry
        if 'geometry' not in self.poreParameters.keys():
            raise KeyError('Geometry was not defined.')
        geom = self.poreParameters['geometry']        
        if (len(geom) != 2): raise NameError(f'Geometry must have two arguments. Arguments given: {geom}')
        # poresize
        if 'poresize' not in self.poreParameters.keys(): raise KeyError('PoreSize was not defined.')
        # script
        if 'runsbatch' not in self.scriptParameters.keys(): raise KeyError('RunSbatch was not determined: Yes or No.')
        if 'stdout' not in self.scriptParameters.keys(): raise KeyError('StdOut file was not defined. Command StdOut [file name]')
        if 'stderr' not in self.scriptParameters.keys(): raise KeyError('StdErr was not defined. Command StdErr [file name]')

    def PrintInputParameters(self):
        programParams = self.programParameters
        stateVars = self.stateVariables
        poreParams = self.poreParameters
        fluidParams = self.fluidParameters
        scriptParams = self.scriptParameters
        print('Input parameters:')
        print('Note: Reduced quantities are expressed in terms of epsilon_ff')
        print('\nSimulation sets, steps and ensemble:')
        for param in programParams.keys(): print(f'{param}: {programParams[param]}')
        print('\nFluid-Fluid parameters:')
        for param in fluidParams.keys(): print(f'{param}: {fluidParams[param]}')
        print('\nSolid-Fluid parameters:')
        for param in poreParams.keys(): print(f'{param}: {poreParams[param]}')
        print('\nState Variables:')
        for param in stateVars.keys(): print(f'{param}: {stateVars[param]}')
        print('\nInput function files:')
        for param in scriptParams.keys(): print(f'{param}: {scriptParams[param]}')
        print('')

    def CreateDirectories(self):
        poreSizes = self.poreParameters['poresize[nm]']
        for d_ext in poreSizes:
            try: os.mkdir(str(d_ext)+'nm')
            except FileExistsError:
                shutil.rmtree(str(d_ext)+'nm')
                os.mkdir(str(d_ext)+'nm')

    def ReadFugacityCoefficient(self):
        pressures = self.stateVariables['externalpressure[Pa]']
        temp = self.stateVariables['externaltemperature[K]']
        epsilon = self.fluidParameters['epsilon_ff[K]']
        mass = self.fluidParameters['molarmass[g/mol]']/avogadro*1e-3 #kg
        thermalWL = planck/np.sqrt(2*np.pi*mass*kb*temp)
        idealRho = pressures/(kb*temp)
        idealMu = temp*np.log(idealRho*thermalWL**3) #K
        mu = 0 #If mu=0, then there was no phi, phi file or mu file given by the user.
        if 'fugacitycoefficient' in self.stateVariables.keys():
            phiValues = self.stateVariables['fugacitycoefficient']
            if len(phiValues) == 1: phiValues = phiValues[0]
            mu = idealMu+temp*np.log(phiValues) #K #Check! phiValues must have either the same length as P or 1.
        elif 'phifile' in self.scriptParameters.keys(): 
            # The phi file must contain a function called Phi=Phi(P,params) for several pressure points, where Phi cannot change its name.
            phiFile = __import__(self.scriptParameters['phifile'][:-3]) 
            params = {**self.fluidParameters, **self.poreParameters, **self.stateVariables}
            phiValues = phiFile.Phi(pressures,params)
            self.stateVariables['fugacitycoefficient'] = phiValues
            mu = idealMu+temp*np.log(phiValues) #K #Check! phi must have the same length as P.
        elif 'mufile' in self.scriptParameters.keys(): mu = self.ReadChemicalPotential(pressures)
        self.stateVariables['chemicalpotential[K]'] = mu
        self.stateVariables['chemicalpotential'] = mu/epsilon
        # Print Mu values
        print(f'chemicalpotential[K]: {mu}')
        print(f'chemicalpotential: {mu/epsilon}\n')

    def ReadChemicalPotential(self,pressures):
        # The mu file must contain a function called Mu=Mu(P,params) for several pressure points, where Mu cannot change its name.
        muFile = __import__(self.scriptParameters['mufile'][:-3]) 
        params = {**self.fluidParameters, **self.poreParameters, **self.stateVariables}
        epsilon = self.fluidParameters['epsilon_ff[K]']
        mu = muFile.Mu(pressures,params)
        return mu

    def WriteSolFile(self):
        if 'usffile' in self.scriptParameters.keys():
            # The Usf file must contain a function called Usf=Usf(x,n_s,eps_ff,eps_sf,sigma_ff,sigma_sf,rcut_ff,rcut_sf) for
            #    for several x points, where x is a vector por positions, rcut can be sigma2 (depending on the potential), 
            #    and variable's names can be different (with the exception of Usf).
            usfFile = __import__(self.scriptParameters['usffile'][:-3]) 
            scriptName = self.scriptParameters['scriptname']
            molName = self.fluidParameters['moleculename']
            eps_ff = self.fluidParameters['epsilon_ff[K]']
            sigma_ff = self.fluidParameters['sigma_ff[nm]']
            molarMass = self.fluidParameters['molarmass[g/mol]']
            poreSizes = self.poreParameters['poresize[nm]']
            reducedPoreSizes = self.poreParameters['poresize']
            n_s = self.poreParameters['n_s[nm^-2]']
            eps_sf = self.poreParameters['epsilon_sf[K]']
            sigma_sf = self.poreParameters['sigma_sf[nm]']
            geom = self.poreParameters['geometry']
            rcut_ff, rcut_sf = 0, 0
            cylinderLength = 40.0 # Usefull only for cylindrical geometries. Otherwise, ignore it.
            nUsfPoints = 2000
            for i in range(len(poreSizes)):
                header = f'## Potential generated by {scriptName} for CHAINBUILD.\n'\
                         f'## Parameters for {molName}: d_ext = {poreSizes[i]} nm, n_s = {n_s} nm^-2, '\
                         f'molarmass = {molarMass} g/mol, eps_ff = {eps_ff} K, eps_sf = {eps_sf} K, '
                # Depending on the potential.
                if 'rcut_ff[nm]' in self.fluidParameters.keys(): 
                    rcut_ff = self.fluidParameters['rcut_ff[nm]']
                    header += f'rcut_ff = {rcut_ff} nm '
                if 'rcut_sf[nm]' in self.poreParameters.keys(): 
                    rcut_sf = self.poreParameters['rcut_sf[nm]']
                    header += f'rcut_sf = {rcut_sf} nm '
                if 'sigma2_ff[nm]' in self.fluidParameters.keys(): 
                    rcut_ff = self.fluidParameters['sigma2_ff[nm]']
                    header += f'sigma2_ff = {rcut_ff} nm '
                if 'sigma2_sf[nm]' in self.poreParameters.keys(): 
                    rcut_sf = self.poreParameters['sigma2_sf[nm]']
                    header += f'sigma2_sf = {rcut_sf} nm '
                header += f'\n'\
                          f'{geom[0]} #{geom[1]}\n'\
                          f'{cylinderLength}\t{reducedPoreSizes[i]}\t{reducedPoreSizes[i]}\n'\
                          f'{nUsfPoints} 0\n'
                # Calculating Usf. Generally, a Usf potential depends on n_s, epsilon (solid or fluid),
                #   sigma (solid or fluid), and rcut (solid or fluid). Therefore, it's mandatory to add these variables,
                #   even if they weren't going to be used.
                params = {**self.fluidParameters, **self.poreParameters, **self.stateVariables}
                if (geom[0] == 1 or geom[0] == 6): 
                    radius = np.linspace(0,poreSizes[i]*0.5,nUsfPoints) #nm
                    potential = usfFile.Usf(radius,params) #K
                    usfPoints = np.vstack((radius,potential)).T
                    header += f'# r(nm)\tU/eps_FF'
                # In progress ...
                # if (geom[0] == 2): 
                    # radius = np.linspace(0,poreSizes[i],nUsfPoints)
                    # theta = np.linspace(0,2*np.pi,nUsfPoints)
                    # x = np.vstack((radius,theta)).T
                    # potential = usfFile.Usf(x,params) #K
                    # header += '# r(nm)\ttheta(°)\tU/eps_FF'
                # if (geom[0] == 3): 
                    # potential = usfFile.Usf(x,y,z,params) #K
                # header += '# x(nm)\ty(nm)\tz(nm)\tU/eps_FF'
                # if (geom[0] == 5): 
                    # potential = usfFile.Usf(z,rho,params) #K
                    # header += '# z(nm)\trho(nm)\tU/eps_FF'
                potential /= eps_ff
                np.savetxt(f'{poreSizes[i]}nm/{molName}.sol',usfPoints,delimiter=' ',header=header,footer='# EOF',comments='')

    def WriteMolFile(self):
        pot_ff = self.fluidParameters['u_ff']
        sigma = self.fluidParameters['sigma_ff[nm]']
        epsilon = self.fluidParameters['epsilon_ff[K]']
        molarMass = self.fluidParameters['molarmass[g/mol]']
        molName = self.fluidParameters['moleculename']
        poreSizes = self.poreParameters['poresize[nm]']
        ensemble = self.programParameters['ensemble']

        fileContent = f'## {pot_ff} {molName}\n'\
                      f'potential {pot_ff}\n'\
                      f'mass {molarMass}\n'\
                      f'epsilon {epsilon}\n'\
                      f'ncut 0\n'
        # Depending on the internal potential.
        if (pot_ff == 'lj'):
            rcut_ff = self.fluidParameters['rcut_ff']
            fileContent += f'sigma {sigma}\n'\
                           f'rcut {rcut_ff}\n'
        if (pot_ff == 'squarewell'):
            sigma2 = self.fluidParameters['sigma2_ff[nm]']
            fileContent += f'sigma1 {sigma}\n'\
                           f'sigma2 {sigma2}\n'
        fileContent += f'end potential {pot_ff}\n#\n'
        # Depending on the chain length and ensemble.
        fileContent += f'moves\n'\
                       f'displacement 1\n'
        if (ensemble == 'nvt'): fileContent += f'exchange 0\n'
        if (ensemble == 'gce'): fileContent += f'exchange 1\n'
        fileContent += f'end moves\n# EOF\n'
        for d_ext in poreSizes:
            molFileName = f'{d_ext}nm/{molName}.mol'
            with open(molFileName,'w') as molFile: molFile.write(fileContent)

    def WriteInputFile(self):
        equilSets = self.programParameters['equilibrationsets'] 
        prodSets = self.programParameters['equilibrationsets']
        stepsPerSet = self.programParameters['stepsperset']
        printEvery = self.programParameters['stepsperset']
        ensemble = self.programParameters['ensemble']
        geom = self.poreParameters['geometry'][1]
        poreSizes = self. poreParameters['poresize[nm]']
        reducedPoreSizes = self.poreParameters['poresize']
        temperature = self.stateVariables['externaltemperature[K]']
        molName = self.fluidParameters['moleculename']
        firstVariable = []
        if (ensemble == 'nvt'): 
            firstVariable = self.stateVariables['numberofmolecules']
        if (ensemble == 'gce'): 
            self.ReadFugacityCoefficient()
            firstVariable = self.stateVariables['chemicalpotential']
        # Writing input file.
        for i in range(len(poreSizes)):
            for var in firstVariable:
                fileContent = f'name {molName}_{var}\n'\
                              f'job {equilSets} {prodSets} {stepsPerSet} {printEvery}\n'\
                              f'ens {ensemble} {var} {temperature}\n'\
                              f'record energy\n'\
                              f'model {molName}.mol\n'\
                              f'summary {molName}_{i}.sum\n'
                if (geom == 'bulk' or geom == 'space' or geom == 'box'): 
                        fileContent += f'solid {geom} {reducedPoreSizes[i]}\n'
                else: fileContent += f'solid {molName}.sol\n'
                fileContent += 'track 3 3\n'\
                               'run\n'
                outFileName = f'{poreSizes[i]}nm/{molName}_{var}.inp'
                with open(outFileName,'w') as outFile: outFile.write(fileContent)

    def WriteSubmitFile(self):
        ensemble = self.programParameters['ensemble']
        runsbatch = self.scriptParameters['runsbatch']
        output = self.scriptParameters['stdout']
        outerr = self.scriptParameters['stderr']
        poreSizes = self.poreParameters['poresize[nm]']
        molName = self.fluidParameters['moleculename']
        firstVariable = []
        if (ensemble == 'nvt'): firstVariable = self.stateVariables['numberofmolecules']
        if (ensemble == 'gce'): firstVariable = self.stateVariables['chemicalpotential']
        poreSizesStr, firstVariableStr = '', ''
        for d_ext in poreSizes: poreSizesStr += str(d_ext)+' '
        for var in firstVariable: firstVariableStr += str(var)+' '
        if runsbatch == 'yes' or runsbatch == 'y':
            # Create an sbatch submit file for each pore size and each number of molecules (or chemical potential).
            for d_ext in poreSizes:
                for var in firstVariable:
                    jobName = self.scriptParameters['jobname']
                    email = self.scriptParameters['email']
                    emailType = self.scriptParameters['emailtype']
                    fileContent = f'#!/bin/sh\n\n'\
                                  f'#SBATCH -J {jobName}\n'\
                                  f'#SBATCH -o {output}\n'\
                                  f'#SBATCH -e {outerr}\n'\
                                  f'#SBATCH --nodes=1\n'\
                                  f'#SBATCH --ntasks=1\n'\
                                  f'#SBATCH --cpus-per-task=1\n'\
                                  f'#SBATCH --mem-per-cpu=1G\n'\
                                  f'#SBATCH --mail-user={email}\n'\
                                  f'#SBATCH --mail-type={emailType}\n'\
                                  f'#SBATCH -p gor\n'\
                                  f'\n'\
                                  f'./../chainbuild < {molName}_{var}.inp\n'
                    submitFileName = f'{d_ext}nm/submit-{molName}_{var}.sh'
                    with open(submitFileName,'w') as submitFile: submitFile.write(fileContent)
            # Create a submit file that executes the remaining submit files.
            fileContent = f'#!/bin/sh\n\n'\
                          f'for d_ext in {poreSizesStr}; do\n'\
                          f'\tcd ${{d_ext}}nm/\n'\
                          f'\tfor var in {firstVariableStr}; do\n'\
                          f'\t\tsbatch submit-{molName}_${{var}}.sh\n'\
                          f'\tdone\n'\
                          f'\tcd ../\n'\
                          f'done\n'
        else: 
            # Create a "parallelized" submit file.
            if 'numberofprocessors' in self.scriptParameters.keys():
                numProcessors = self.scriptParameters['numberofprocessors']
            else: numProcessors = 1
            fileContent = f'#!/bin/sh\n\n'\
                          f'np={numProcessors}\n'\
                          f'for d_ext in {poreSizesStr}; do\n'\
                          f'\tcd ${{d_ext}}nm/\n'\
                          f'\tfor var in {firstVariableStr}; do\n'\
                          f'\t\tjob=$(ps aux | more | grep "./../chainbuild" | head -n -1 | wc -l)\n'\
                          f'\t\tif [[ $job -lt $np ]]; then\n'\
                          f'\t\t\t./../chainbuild < {molName}_${{var}}.inp 1> {output} 2> {outerr} &\n'\
                          f'\t\tfi\n'\
                          f'\t\tsleep 1\n'\
                          f'\tdone\n'\
                          f'\tcd ../\n'\
                          f'done\n'
        submitFileName = f'submit-{molName}.sh'
        with open(submitFileName,'w') as submitFile: submitFile.write(fileContent)
#------------------------------------------------------------------------------------------------------------#
if __name__ == '__main__':
    argv = sys.argv
    system = System(argv)
    if re.search(r'-h.*',' '.join(argv),re.IGNORECASE): system.Help() 
    print('Reading input parameters ...\n')
    system.ReadFileOfInputParameters()
    system.CheckErrors()
    system.PrintInputParameters()
    print('Setting simulation ...\n')
    system.CreateDirectories()
    system.WriteMolFile()
    system.WriteInputFile()
    system.WriteSolFile()
    system.WriteSubmitFile()
    print('Simulation set!\n')
    print('Don\'t forget to add the Chainbuild\'s executable to this path.')
#EOS
