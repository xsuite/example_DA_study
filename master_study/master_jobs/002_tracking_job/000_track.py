import json
import yaml
import time
import logging

import numpy as np
import pandas as pd

import xtrack as xt
import xpart as xp

####################
# Read config file #
####################

with open('config.yaml','r') as fid:
    config=yaml.safe_load(fid)

######################
# Tag job as started #
######################

try:
    import tree_maker
    tree_maker.tag_json.tag_it(config['log_file'], 'started')
except ImportError:
    logging.warning('tree_maker not available')
    tree_maker = None

##########################################
# Read line, part_on_co, one-turn matrix #
##########################################

with open(config['xline_json']) as fid:
    dd=json.load(fid)

p_co = xp.Particles.from_dict(dd['particle_on_tracker_co'])
line = xt.Line.from_dict(dd)
R_matrix = np.array(dd['RR_finite_diffs'])

#####################################################
# Get normalized coordinateds of particles to track #
#####################################################

particle_df=pd.read_parquet(config['particle_file'])

r_vect = particle_df['normalized amplitude in xy-plane'].values
theta_vect = particle_df['angle in xy-plane [deg]'].values*np.pi/180 # [rad]

A1_in_sigma = r_vect * np.cos(theta_vect)
A2_in_sigma = r_vect * np.sin(theta_vect)

####################################################
# Generate particles object (physical coordinates) #
####################################################

particles = xp.build_particles(
        particle_on_co=p_co,
        x_norm=A1_in_sigma, y_norm=A2_in_sigma,
        delta = config['delta_max'],
        R_matrix=R_matrix,
        scale_with_transverse_norm_emitt=(config['epsn_1'], config['epsn_2']))
particles.particle_id = particle_df.particle_id.values

#################
# Symplify line #
#################

#line.remove_inactive_multipoles(inplace=True)
#line.remove_zero_length_drifts(inplace=True)
#line.merge_consecutive_drifts(inplace=True)
#line.merge_consecutive_multipoles(inplace=True)

#################
# Build tracker #
#################

tracker = xt.Tracker(line=line)

############################
# Save initial coordinates # 
############################

pd.DataFrame(particles.to_dict()).to_parquet('input_particles.parquet')

##########
# Track! #
##########

num_turns = config['n_turns']
a=time.time()
tracker.track(particles, turn_by_turn_monitor=False, num_turns=num_turns)
b=time.time()

print(f'Elapsed time: {b-a} s')
print(f'Elapsed time per particle per turn: {(b-a)/particles._capacity/num_turns*1e6} us')

##########################
# Save final coordinates # 
##########################

pd.DataFrame(particles.to_dict()).to_parquet('output_particles.parquet')

if tree_maker is not None:
    tree_maker.tag_json.tag_it(config['log_file'], 'completed')
