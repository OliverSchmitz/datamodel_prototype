'''
@author: Merijn de Bakker, Utrecht University 2016
'''

import sys
import os.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import grazing as grazing
import mapalgebra.model_setup as model_setup
import model_runner

if len(sys.argv) is 1:
    n_of_timesteps = 50
else:
    n_of_timesteps = int(sys.argv[1])

# initialize(setup). setup test data, etcetera
model_runner.initialize(model_setup)

# run(model, number_of_timesteps
model_runner.run(grazing, n_of_timesteps)

# finalize the model run
model_runner.finalize()
