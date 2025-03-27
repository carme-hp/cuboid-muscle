#include <Python.h>
#include <iostream>
#include <cstdlib>

#include <iostream>
#include "easylogging++.h"

#include "opendihu.h"

int main(int argc, char *argv[])
{
  DihuContext settings(argc, argv);
  
  Control::PreciceAdapter<
    TimeSteppingScheme::DynamicHyperelasticitySolver<
        Equation::SolidMechanics::SaintVenantKirchhoff
    > 
  > problem(settings);
  
  problem.run();
  
  return EXIT_SUCCESS;
}