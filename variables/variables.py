import sys
import itertools
import numpy as np

rank_no = int(sys.argv[-2])
n_ranks = int(sys.argv[-1])

# Timestep
#################################################################

dt_3D = .5             # time step of 3D mechanics
dt_splitting = 2e-3     # time step of strang splitting
dt_1D = 2e-3            # time step of 1D fiber diffusion
dt_0D = 1e-3            # time step of 0D cellml problem
end_time = 20.0         # end time of the simulation 
output_interval = dt_3D # time interval between outputs

# Muscle mechanics
#################################################################

# Mesh
muscle_extent = [3.0, 3.0, 12.0]               
muscle_offset = [0.0, 0.0, 0.0]
n_elements = [4, 4, 16]                

meshes = {

  "muscleMesh": {
    "nElements" :         n_elements,
    "physicalExtent":     muscle_extent,
    "physicalOffset":     muscle_offset,
    "inputMeshIsGlobal":  True,
    "nRanks":             n_ranks
  },

  # needed for mechanics solver
  "muscleMesh_quadratic": {
    "nElements" :         [elems // 2 for elems in n_elements],
    "physicalExtent":     muscle_extent,
    "physicalOffset":     muscle_offset,
    "inputMeshIsGlobal":  True,
    "nRanks":             n_ranks,
  }
}

# Boundary conditions
[nx, ny, nz] = [elem + 1 for elem in n_elements]
[mx, my, mz] = [elem // 2 for elem in n_elements]

dirichlet_bc = {} 
kd = nz-1 # set to 0 for left end and to nz-1 for right end
for j in range(ny):
  for i in range(nx):
    dirichlet_bc[kd*nx*ny + j*nx + i] = [0.0, 0.0, 0.0, None,None,None] # displacement ux uy uz, velocity vx vy vz

neumann_force = 0 #TODO
neumann_bc = [] 
kn = 0 # set to 0 for left end and to mz-1 for right end
for x in range(mx):
    for y in range(my):
        neumann_bc += [{
            "element": x + y*mx + (kn)*mx*my, 
            "constantVector": [0, 0, neumann_force], 
            "face": "2+"
        }]

# Material parameters
pmax = 7.3                                                  # maximum active stress
rho = 10                                                    # density of the muscle
material_parameters = [3.176e-10, 1.813, 1.075e-2, 1.0]     # [c1, c2, b, d]

# Muscle Fibers
#################################################################

# Meshes
fb_x, fb_y = 8, 8         # TODO: number of fibers
fb_points = 100             # TODO: number of points per fiber


def get_fiber_no(fiber_x, fiber_y):
    return fiber_x + fiber_y*fb_x

for fiber_x in range(fb_x):
    for fiber_y in range(fb_y):
        fiber_no = get_fiber_no(fiber_x, fiber_y)
        x = muscle_extent[0] * fiber_x / (fb_x - 1)
        y = muscle_extent[1] * fiber_y / (fb_y - 1)
        nodePositions = [[x, y, muscle_offset[2] + muscle_extent[2] * i / (fb_points - 1)] for i in range(fb_points)]
        meshName = "fiber{}".format(fiber_no)
        meshes[meshName] = { # create fiber meshes
            "nElements":            [fb_points - 1],
            "nodePositions":        nodePositions,
            "inputMeshIsGlobal":    True,
            "nRanks":               n_ranks
        }

# material parameters
diffusion_prefactor = 3.828 / (500.0 * 0.58)                # Conductivity / (Am * Cm)

# stimulation parameters
specific_states_call_enable_begin = 0.0                     # time of first fiber activation
specific_states_call_frequency = 1e-3                       # frequency of fiber activation
neuromuscular_junction_relative_size =.0
value_for_stimulated_point = 20 #mV


# Input files for fibers
#################################################################

import os
input_dir = os.path.join(os.environ.get('OPENDIHU_HOME', '../../../../../../../'), "examples/electrophysiology/input/")

cellml_file = input_dir + "hodgkin_huxley-razumova.cellml" #TODO

fiber_distribution_file = input_dir + "MU_fibre_distribution_10MUs.txt"
firing_times_file = input_dir + "MU_firing_times_always.txt"

# Write to file
#################################################################

def get_from_obj(data, path):
    for elem in path:
        if type(elem) == str:
            data = data[elem]
        elif type(elem) == int:
            data = data[elem]
        elif type(elem) == tuple:
            # search for key == value with (key, value) = elem
            key, value = elem
            data = next(filter(lambda e: e[key] == value, data))
        else:
            raise KeyError(f"Unknown type of '{elem}': '{type(elem)}'. Path: '{'.'.join(path)}'")
    return data

def write_average_position(data):
    t = get_from_obj(data, [0, 'currentTime'])
    z_data = get_from_obj(data, [0, 'data', ('name','geometry'), 'components', 2, 'values'])

    [mx, my, mz] = get_from_obj(data, [0, 'nElementsLocal'])
    nx = 2*mx + 1
    ny = 2*my + 1
    nz = 2*mz + 1
    # compute average z-value of end of muscle
    z_value_begin = 0.0
    z_value_end = 0.0

    for j in range(ny):
        for i in range(nx):
            z_value_begin += z_data[j*nx + i]
            z_value_end += z_data[(nz-1)*nx*ny + j*nx + i]


    z_value_begin /= ny*nx
    z_value_end /= ny*nx


    f = open("muscle_position.txt", "a")
    f.write("{:6.2f} {:+2.8f} {:+2.8f}\n".format(t,z_value_begin, z_value_end))
    f.close()

