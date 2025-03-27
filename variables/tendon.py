import sys
import itertools
import numpy as np

rank_no = int(sys.argv[-2])
n_ranks = int(sys.argv[-1])

scenario_name = "tendon" 

# Tendon mechanics
#################################################################

# Mesh
tendon_extent = [3.0, 3.0, 4.0]               
tendon_offset = [0.0, 0.0, 12.0]
n_elements = [4, 4, 4]                

meshes = {

  "tendonMesh": {
    "nElements" :         n_elements,
    "physicalExtent":     tendon_extent,
    "physicalOffset":     tendon_offset,
    "inputMeshIsGlobal":  True,
    "nRanks":             n_ranks
  },

  # needed for mechanics solver
  "tendonMesh_quadratic": {
    "nElements" :         [elems // 2 for elems in n_elements],
    "physicalExtent":     tendon_extent,
    "physicalOffset":     tendon_offset,
    "inputMeshIsGlobal":  True,
    "nRanks":             n_ranks,
  }
}

# Boundary conditions
[nx, ny, nz] = [elem + 1 for elem in n_elements]
[mx, my, mz] = [elem // 2 for elem in n_elements]

dirichlet_bc = {} 

for k in range(nz):
  dirichlet_bc[k*nx*ny] = [0.0, 0.0, None, None, None, None] # displacement ux uy uz, velocity vx vy vz
  dirichlet_bc[k*nx*ny + nx-1] = [0.0, 0.0, None, None, None, None] # displacement ux uy uz, velocity vx vy vz
  dirichlet_bc[k*nx*ny + ny*(nx-1)] = [0.0, 0.0, None, None, None, None] # displacement ux uy uz, velocity vx vy vz
  dirichlet_bc[k*nx*ny + ny*(nx-1) + nx -1] = [0.0, 0.0, None, None, None, None] # displacement ux uy uz, velocity vx vy vz

neumann_bc = [] 

# Material parameters
rho = 10                                                    # density of the muscle


youngs_modulus = 7e4        # [N/cm^2 = 10kPa]  
shear_modulus = 3e4

lambd = shear_modulus*(youngs_modulus - 2*shear_modulus) / (3*shear_modulus - youngs_modulus)  # Lamé parameter lambda
mu = shear_modulus       # Lamé parameter mu or G (shear modulus)

material_parameters = [lambd, mu]


c = 9.98                    # [N/cm^2=kPa]
ca = 14.92                  # [-]
ct = 14.7                   # [-]
cat = 9.64                  # [-]
ctt = 11.24                 # [-]
mu = 3.76                   # [N/cm^2=kPa]
k1 = 42.217e3               # [N/cm^2=kPa]
k2 = 411.360e3              # [N/cm^2=kPa]

#material_parameters = [c, ca, ct, cat, ctt, mu, k1, k2]

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

