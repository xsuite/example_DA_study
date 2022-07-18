# %%
import tree_maker
from tree_maker import NodeJob
from tree_maker import initialize
import time
import os
from pathlib import Path
import itertools
import numpy as np
import yaml
from user_defined_functions import generate_run_sh
from user_defined_functions import generate_run_sh_htc

# Import the configuration
config=yaml.safe_load(open('config.yaml'))


# The user defines the variable to scan
# machine parameters scans
qx0 = np.arange(62.305, 62.330, 0.001)[::20]
qy0 = np.arange(60.305, 60.330, 0.001)[::20]

children={}
for optics_job, (myq1, myq2) in enumerate(itertools.product(qx0, qy0)):
    optics_children={}
    children[f'{optics_job:03}'] = {
                                    'qx0':float(myq1),
                                    'qy0':float(myq2),
                                    'children':optics_children}
    for track_job in range(15):
        optics_children[f'{track_job:03}'] = {
                    'particle_file': ('../../'
                                   f'distrib_abc/{track_job:03}.parquet'),
                    'xline_json': ('../xsuite_lines/'
                                  'line_bb_for_tracking.json'),
                    'n_turns': int(1000)}

if config['root']['use_yaml_children']== False:
    config['root']['children'] = children
config['root']['setup_env_script'] = os.getcwd() + '/../miniconda/bin/activate'

# Create tree object
start_time = time.time()
root = initialize(config)
print('Done with the tree creation.')
print("--- %s seconds ---" % (time.time() - start_time))

# From python objects we move the nodes to the file-system.
start_time = time.time()
#root.make_folders(generate_run_sh)
root.make_folders(generate_run_sh_htc)
print('The tree folders are ready.')
print("--- %s seconds ---" % (time.time() - start_time))
