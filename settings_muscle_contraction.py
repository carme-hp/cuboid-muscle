import sys
import os
import itertools
import importlib

# parse arguments
rank_no = (int)(sys.argv[-2])
n_ranks = (int)(sys.argv[-1])

# add folders to python path
script_path = os.path.dirname(os.path.abspath(__file__))
var_path = os.path.join(script_path, "variables")
sys.path.insert(0, var_path)

import variables

# if first argument contains "*.py", it is a custom variable definition file, load these values
if ".py" in sys.argv[0]:
  variables_path_and_filename = sys.argv[0]
  variables_path,variables_filename = os.path.split(variables_path_and_filename)  # get path and filename 
  sys.path.insert(0, os.path.join(script_path,variables_path))                    # add the directory of the variables file to python path
  variables_module,_ = os.path.splitext(variables_filename)                       # remove the ".py" extension to get the name of the module
  
  if rank_no == 0:
    print("Loading variables from \"{}\".".format(variables_path_and_filename))
    
  custom_variables = importlib.import_module(variables_module, package=variables_filename)    # import variables module
  variables.__dict__.update(custom_variables.__dict__)
  sys.argv = sys.argv[1:]     # remove first argument, which now has already been parsed
else:
  if rank_no == 0:
    print("Warning: There is no variables file, e.g:\n ./fibers ../settings_fibers.py fibers.py\n")
  exit(0)

scenario_name = "muscle-contraction" 

# define config
config = {
  "scenarioName":                   scenario_name,

  "logFormat":                      "csv",
  "mappingsBetweenMeshesLogFile":   "out/" + scenario_name + "/mappings_between_meshes.txt",
  "solverStructureDiagramFile":     "out/" + scenario_name + "/solver_structure.txt",
  
  "Meshes":                         variables.meshes,
  "MappingsBetweenMeshes": { 
      "mesh3D" : ["fiber{}".format(variables.get_fiber_no(fiber_x, fiber_y)) for fiber_x in range(variables.fb_x) for fiber_y in range(variables.fb_y)]
  },

  "Solvers": {
    "diffusionSolver": {
      "solverType":                     "cg",
      "preconditionerType":             "none",
      "relativeTolerance":              1e-10,
      "absoluteTolerance":              1e-10,
      "maxIterations":                  1e4,
      "dumpFilename":                   "",
      "dumpFormat":                     "matlab"
    },
    "mechanicsSolver": {
      "solverType":                     "preonly",
      "preconditionerType":             "lu",
      "relativeTolerance":              1e-10,
      "absoluteTolerance":              1e-10,
      "maxIterations":                  1e4,
      "snesLineSearchType":             "l2",
      "snesRelativeTolerance":          1e-5,
      "snesAbsoluteTolerance":          1e-5,
      "snesMaxIterations":              10,
      "snesMaxFunctionEvaluations":     1e8,
      "snesRebuildJacobianFrequency":   5,
      "dumpFilename":                   "",
      "dumpFormat":                     "matlab"
    }
  },

  "Coupling": {
    "timeStepWidth":            variables.dt_3D,
    "logTimeStepWidthAsKey":    "dt_3D",
    "durationLogKey":           "duration_3D",
    "endTime":                  variables.end_time,
    "timeStepOutputInterval":   1,
    "connectedSlotsTerm1To2":   {1:2},  # transfer stress to MuscleContractionSolver gamma
    "connectedSlotsTerm2To1":   None,   # transfer nothing back

    "Term1": { # fibers (FastMonodomainSolver)
      "MultipleInstances": { 
        "ranksAllComputedInstances":    list(range(n_ranks)),
        "nInstances":                   1,

        "instances": [{
          "ranks": [0],

          "StrangSplitting": {
            "timeStepWidth":            variables.dt_splitting,
            "logTimeStepWidthAsKey":    "dt_splitting",
            "durationLogKey":           "duration_splitting",
            "timeStepOutputInterval":   100,
            "connectedSlotsTerm1To2":   None,
            "connectedSlotsTerm2To1":   None,

            "Term1": { # reaction term
              "MultipleInstances": {
                "nInstances":   variables.fb_x * variables.fb_y,

                "instances": [{
                  "ranks": [0],

                  "Heun": {
                    "timeStepWidth":            variables.dt_0D,
                    "logTimeStepWidthAsKey":    "dt_0D",
                    "durationLogKey":           "duration_0D",
                    "timeStepOutputInterval":   100,

                    "initialValues":                [],
                    "dirichletBoundaryConditions":  {},
                    "dirichletOutputFilename":      None,
                    "inputMeshIsGlobal":            True,
                    "checkForNanInf":               False,
                    "nAdditionalFieldVariables":    0,
                    "additionalSlotNames":          [],
                    "OutputWriter":                 [],

                    "CellML": {
                      "modelFilename":          variables.cellml_file,
                      "meshName":               "fiber{}".format(variables.get_fiber_no(fiber_x, fiber_y)), 
                      "stimulationLogFilename": "out/" + scenario_name + "stimulation.log",

                      "statesInitialValues":                        [],
                      "initializeStatesToEquilibrium":              False,
                      "initializeStatesToEquilibriumTimeStepWidth": 1e-4,
                      "optimizationType":                           "vc",
                      "approximateExponentialFunction":             True,
                      "compilerFlags":                              "-fPIC -O3 -march=native -Wno-deprecated_declarations -shared",
                      "maximumNumberOfThreads":                     0,

                      "setSpecificStatesCallEnableBegin":       variables.specific_states_call_enable_begin,
                      "setSpecificStatesCallFrequency":         variables.specific_states_call_frequency,
                      "setSpecificStatesRepeatAfterFirstCall":  0.01,
                      "setSpecificStatesFrequencyJitter":       [0] ,
                      "setSpecificStatesCallInterval":          0,
                      "setSpecificStatesFunction":              None,
                      "additionalArgument":                     None, 

                      "mappings": {
                        ("parameter", 0):               "membrane/i_Stim",
                        ("parameter", 1):               "Razumova/l_hs",
                        ("parameter", 2):               ("constant", "Razumova/rel_velo"),
                        ("connectorSlot", "vm"):        "membrane/V",
                        ("connectorSlot", "stress"):    "Razumova/activestress",
                        ("connectorSlot", "alpha"):     "Razumova/activation",
                        ("connectorSlot", "lambda"):    "Razumova/l_hs",
                        ("connectorSlot", "ldot"):      "Razumova/rel_velo"
                      },
                      "parametersInitialValues": [0.0, 1.0, 0.0],
                    },
                  }
                } for fiber_x in range(variables.fb_x) for fiber_y in range(variables.fb_y)] 
              }
            },

            "Term2": { # diffusion term
              "MultipleInstances": {
                "nInstances": variables.fb_x * variables.fb_y, 

                "OutputWriter": [
                  {
                    "format":         "Paraview",
                    "outputInterval": int(1.0 / variables.dt_splitting * variables.output_interval),
                    "filename":       "out/" + scenario_name + "/fibers",
                    "fileNumbering":  "incremental",
                    "binary":         True,
                    "fixedFormat":    False,
                    "combineFiles":   True
                  }
                ],

                "instances": [{
                  "ranks": [0],

                  "ImplicitEuler": {
                    "timeStepWidth":            variables.dt_1D,
                    "logTimeStepWidthAsKey":    "dt_1D",
                    "durationLogKey":           "duration_1D",
                    "timeStepOutputInterval":   100,

                    "nAdditionalFieldVariables":    4,
                    "additionalSlotNames":          ["stress", "alpha", "lambda", "ldot"],

                    "solverName":                       "diffusionSolver",
                    "timeStepWidthRelativeTolerance":   1e-10,

                    "dirichletBoundaryConditions":      {},
                    "dirichletOutputFilename":          None,
                    "inputMeshIsGlobal":                True,
                    "checkForNanInf":                   False,
                    "OutputWriter":                     [],

                    "FiniteElementMethod": {
                      "meshName":           "fiber{}".format(variables.get_fiber_no(fiber_x, fiber_y)),
                      "inputMeshIsGlobal":  True,
                      "solverName":         "diffusionSolver",
                      "prefactor":          variables.diffusion_prefactor,
                      "slotName":           "vm"
                    }
                  }
                } for fiber_x in range(variables.fb_x) for fiber_y in range(variables.fb_y)]
              }
            }
          }
        }]
      },

      "fiberDistributionFile":                              variables.fiber_distribution_file,
      "firingTimesFile":                                    variables.firing_times_file,
      "valueForStimulatedPoint":                            variables.value_for_stimulated_point,
      "onlyComputeIfHasBeenStimulated":                     True,
      "disableComputationWhenStatesAreCloseToEquilibrium":  True,
      "neuromuscularJunctionRelativeSize":                  variables.neuromuscular_junction_relative_size,
      "generateGPUSource":                                  True,
      "useSinglePrecision":                                 False
    },

    "Term2": { # solid mechanics (MuscleContractionSolver)
      "MuscleContractionSolver": {
        "Pmax":                         variables.pmax,
        "slotNames":                    ["lambda", "ldot", "gamma", "T"],
        "dynamic":                      True,

        "numberTimeSteps":              1,
        "timeStepOutputInterval":       100,
        "lambdaDotScalingFactor":       1,
        "enableForceLengthRelation":    True,
        "mapGeometryToMeshes":          [],

        "OutputWriter": [
          {
            "format":             "Paraview",
            "outputInterval":     int(1.0 / variables.dt_3D * variables.output_interval),
            "filename":           "out/" + scenario_name + "/muscle",
            "fileNumbering":      "incremental",
            "binary":             True,
            "fixedFormat":        False,
            "onlyNodalValues":    True,
            "combineFiles":       True
          }
        ],

        "DynamicHyperelasticitySolver": {
          "durationLogKey":         "duration_3D",
          "logTimeStepWidthAsKey":  "dt_3D",
          "numberTimeSteps":        1,
          "materialParameters":     variables.material_parameters,
          "density":                variables.rho,
          "timeStepOutputInterval": 1,

          "meshName":                   "muscleMesh_quadratic",
          "fiberDirectionInElement":    [0,0,1],
          "inputMeshIsGlobal":          True,
          "fiberMeshNames":             [],
          "fiberDirection":             None,

          "solverName":                 "mechanicsSolver",
          "displacementsScalingFactor":  1.0,
          "useAnalyticJacobian":        True,
          "useNumericJacobian":         False,
          "dumpDenseMatlabVariables":   False,
          "loadFactorGiveUpThreshold":  1,
          "loadFactors":                [],
          "scaleInitialGuess":          False,
          "extrapolateInitialGuess":    True,
          "nNonlinearSolveCalls":       1,

          "dirichletBoundaryConditions":                            variables.dirichlet_bc,
          "neumannBoundaryConditions":                              variables.neumann_bc,
          "updateDirichletBoundaryConditionsFunction":              None,
          "updateDirichletBoundaryConditionsFunctionCallInterval":  1,
          "divideNeumannBoundaryConditionValuesByTotalArea":        True,

          "initialValuesDisplacements": [[0, 0, 0] for _ in range(variables.nx * variables.ny * variables.nz)],
          "initialValuesVelocities":    [[0, 0, 0] for _ in range(variables.nx * variables.ny * variables.nz)],
          "constantBodyForce":          (0, 0, 0),

          "dirichletOutputFilename":    "out/" + scenario_name + "/dirichlet_output",
          "residualNormLogFilename":    "out/" + scenario_name + "/residual_norm_log.txt",
          "totalForceLogFilename":      "out/" + scenario_name + "/total_force_log.txt",

          "OutputWriter": [
            {"format": "PythonCallback", "outputInterval": 1, "callback": variables.write_average_position, "onlyNodalValues":True, "filename": "", "fileNumbering":'incremental'},

          ],
          "pressure":       { "OutputWriter": [] },
          "dynamic":        { "OutputWriter": [] },
          "LoadIncrements": { "OutputWriter": [] }
        }
      }
    }
  }
}