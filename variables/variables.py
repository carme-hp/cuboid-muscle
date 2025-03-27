precice_file = "../precice-config.xml"

# Timestep
#################################################################

dt_3D = 0.01             # time step of 3D mechanics
dt_splitting = 2e-3     # time step of strang splitting
dt_1D = 2e-3            # time step of 1D fiber diffusion
dt_0D = 1e-3            # time step of 0D cellml problem
end_time = 20.0         # end time of the simulation 
output_interval = dt_3D # time interval between outputs
