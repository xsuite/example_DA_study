# ==================================================================================================
# --- Imports
# ==================================================================================================
from tree_maker import initialize
import time
import os
import itertools
import numpy as np
import yaml
import shutil
import copy
import json
from user_defined_functions import (
    generate_run_sh_htc,
    get_worst_bunch,
    reformat_filling_scheme_from_lpc,
)

# ==================================================================================================
# --- Initial particle distribution parameters (generation 1)
#
# Below, the user defines the parameters for the initial particles distribution.
# Path for the particle distribution configuration:
# mmaster_study/master_jobs/1_build_distr_and_collider/config_collider.yaml [field config_particles]
# ==================================================================================================

# Define dictionary for the initial particle distribution
d_config_particles = {}

# Radius of the initial particle distribution
d_config_particles["r_min"] = 2
d_config_particles["r_max"] = 10
d_config_particles["n_r"] = 2 * 16 * (d_config_particles["r_max"] - d_config_particles["r_min"])

# Number of angles for the initial particle distribution
d_config_particles["n_angles"] = 5

# Number of split for parallelization
d_config_particles["n_split"] = 8

# ==================================================================================================
# --- Optics collider parameters (generation 1)
#
# Below, the user defines the optics collider parameters. These parameters cannot be scanned.
# Path for the collider configuration:
# master_study/master_jobs/1_build_distr_and_collider/config_collider.yaml [field config_collider]
# ==================================================================================================

### Mad configuration

# Define dictionary for the Mad configuration
d_config_mad = {"beam_config": {"lhcb1": {}, "lhcb2": {}}}

# Optic file path (round or flat)
d_config_mad["optics_file"] = "acc-models-lhc/flatcc/opt_flathv_75_180_1500_thin.madx"

# Beam energy (for both beams)
beam_energy_tot = 7000
d_config_mad["beam_config"]["lhcb1"]["beam_energy_tot"] = beam_energy_tot
d_config_mad["beam_config"]["lhcb2"]["beam_energy_tot"] = beam_energy_tot


# ==================================================================================================
# --- Base collider parameters (generation 2)
#
# Below, the user defines the standard collider parameters. Some of the values defined here are
# later updated according to the grid-search being done.
# Path for the collider config:
# master_study/master_jobs/2_configure_and_track/config.yaml [field config_collider]
# ==================================================================================================

### Tune and chroma configuration

# Define dictionnary for tune and chroma
d_config_tune_and_chroma = {
    "qx": {},
    "qy": {},
    "dqx": {},
    "dqy": {},
}
for beam in ["lhcb1", "lhcb2"]:
    d_config_tune_and_chroma["qx"][beam] = 62.313
    d_config_tune_and_chroma["qy"][beam] = 60.320
    d_config_tune_and_chroma["dqx"][beam] = 5.0
    d_config_tune_and_chroma["dqy"][beam] = 5.0

# Value to be added to linear coupling knobs
d_config_tune_and_chroma["delta_cmr"] = 0.001
d_config_tune_and_chroma["delta_cmi"] = 0.0

### Knobs configuration

# Define dictionary for the knobs settings
d_config_knobs = {}

# Knobs at IPs
d_config_knobs["on_x1"] = 250
d_config_knobs["on_sep1"] = 0
d_config_knobs["on_x2"] = -170
d_config_knobs["on_sep2"] = 0.138
d_config_knobs["on_x5"] = 250
d_config_knobs["on_sep5"] = 0
d_config_knobs["on_x8h"] = 0.0
d_config_knobs["on_x8v"] = 170

# Crab cavities
d_config_knobs["on_crab1"] = -190
d_config_knobs["on_crab5"] = -190

# Octupoles
d_config_knobs["i_oct_b1"] = 60.0
d_config_knobs["i_oct_b2"] = 60.0

### leveling configuration

# Define dictionary for the leveling settings
d_config_leveling = {"ip2": {}, "ip8": {}}

# Luminosity and particles

# skip_leveling should be set to True if the study is done at start of leveling
skip_leveling = False

# Leveling parameters (ignored if skip_leveling is True)
d_config_leveling["ip2"]["separation_in_sigmas"] = 5
d_config_leveling["ip8"]["luminosity"] = 2.0e33
# "num_colliding_bunches" is set in the 1_build_distr_and_collider script, depending on the filling scheme

### Beam beam configuration

# Define dictionary for the beam beam settings
d_config_beambeam = {"mask_with_filling_pattern": {}}

# Beam settings
d_config_beambeam["num_particles_per_bunch"] = 1.4e11 * (1960 / 2216) ** 0.5
d_config_beambeam["nemitt_x"] = 2.5e-6
d_config_beambeam["nemitt_y"] = 2.5e-6

# Filling scheme (in json format)
# The scheme should consist of a json file containing two lists of booleans (one for each beam),
# representing each bucket of the LHC.
filling_scheme_path = os.path.abspath(
    "master_jobs/filling_scheme/25ns_2228b_2216_1686_2112_hybrid_8b4e_2x56b_25ns_3x48b_12inj_with_identical_bunches.json"
)

# Alternatively, one can get a fill directly from LPC from, e.g.:
# https://lpc.web.cern.ch/cgi-bin/fillTable.py?year=2023
# In this page, get the fill number of your fill of interest, and use it to replace the XXXX in the
# URL below before downloading:
# https://lpc.web.cern.ch/cgi-bin/schemeInfo.py?fill=XXXX&fmt=json
# Unfortunately, the format is not the same as the one used by defaults in xmask, but it should
# still be converted in the lines below (see with matteo.rufolo@cern.ch for questions, or if it
# doesn't work).

# Load filling scheme
if filling_scheme_path.endswith(".json"):
    with open(filling_scheme_path, "r") as fid:
        d_filling_scheme = json.load(fid)

# If the filling scheme is already in the correct format, do nothing
if "beam1" in d_filling_scheme.keys() and "beam2" in d_filling_scheme.keys():
    pass
# Otherwise, we need to reformat the file
else:
    # One can potentially use b1_array, b2_array to scan the bunches later
    b1_array, b2_array = reformat_filling_scheme_from_lpc(filling_scheme_path)
    filling_scheme_path = filling_scheme_path.replace(".json", "_converted.json")


# Add to config file
d_config_beambeam["mask_with_filling_pattern"][
    "pattern_fname"
] = filling_scheme_path  # If None, a full fill is assumed


# Set this variable to False if you intend to scan the bunch number (but ensure both bunches indices
# are defined later)
d_config_beambeam["mask_with_filling_pattern"]["i_bunch_b1"] = None
d_config_beambeam["mask_with_filling_pattern"]["i_bunch_b2"] = 1144
check_bunch_number = False
if check_bunch_number:
    # Bunch number (ignored if pattern_fname is None (in which case the simulation considers all bunch
    # elements), must be specified otherwise)
    # If the bunch number is None and pattern_name is defined, the bunch with the largest number of
    # long-range interactions will be used

    if d_config_beambeam["mask_with_filling_pattern"]["i_bunch_b1"] is None:
        # Case the bunch number has not been provided
        worst_bunch_b1 = get_worst_bunch(
            filling_scheme_path, numberOfLRToConsider=26, beam="beam_1"
        )
        while d_config_beambeam["mask_with_filling_pattern"]["i_bunch_b1"] is None:
            bool_inp = input(
                "The bunch number for beam 1 has not been provided. Do you want to use the bunch"
                " with the largest number of long-range interactions? It is the bunch number "
                + str(worst_bunch_b1)
                + " (y/n): "
            )
            if bool_inp == "y":
                d_config_beambeam["mask_with_filling_pattern"]["i_bunch_b1"] = worst_bunch_b1
            elif bool_inp == "n":
                d_config_beambeam["mask_with_filling_pattern"]["i_bunch_b1"] = int(
                    input("Please enter the bunch number for beam 1: ")
                )

    if d_config_beambeam["mask_with_filling_pattern"]["i_bunch_b2"] is None:
        worst_bunch_b2 = get_worst_bunch(
            filling_scheme_path, numberOfLRToConsider=26, beam="beam_2"
        )
        # For beam 2, just select the worst bunch by default, as the tracking of b2 is not available yet anyway
        print(
            "The bunch number for beam 2 has not been provided. By default, the worst bunch is"
            " taken. It is the bunch number "
            + str(worst_bunch_b2)
        )
        d_config_beambeam["mask_with_filling_pattern"]["i_bunch_b2"] = worst_bunch_b2


# ==================================================================================================
# --- Generate dictionnary to encapsulate all base collider parameters (generation 2)
# ==================================================================================================
d_config_collider = {}

# Add tunes and chromas
d_config_collider["config_knobs_and_tuning"] = d_config_tune_and_chroma

# Add knobs
d_config_collider["config_knobs_and_tuning"]["knob_settings"] = d_config_knobs

# Add luminosity configuration
d_config_collider["skip_leveling"] = skip_leveling
d_config_collider["config_lumi_leveling"] = d_config_leveling

# Add beam beam configuration
d_config_collider["config_beambeam"] = d_config_beambeam

# ==================================================================================================
# --- Tracking parameters (generation 2)
#
# Below, the user defines the parameters for the tracking.
# ==================================================================================================
d_config_simulation = {}

# Number of turns to track
d_config_simulation["n_turns"] = 1000000

# Initial off-momentum
d_config_simulation["delta_max"] = 27.0e-5

# Beam to track (lhcb1 or lhcb2)
d_config_simulation["beam"] = "lhcb1"
# ==================================================================================================
# --- Machine parameters being scanned (generation 2)
#
# Below, the user defines the grid for the machine parameters that must be scanned to find the
# optimal DA (e.g. tune, chroma, etc).
# ==================================================================================================
# Scan first bunch of each family
l_bunch_to_scan = []
for l_of_bunch_per_family in d_filling_scheme["beam1_identical_bunches"]:
    l_bunch_to_scan.append(int(l_of_bunch_per_family[0]))

l_bunch_to_scan = l_bunch_to_scan
# ==================================================================================================
# --- Make tree for the simulations (generation 1)
#
# The tree is built as a hierarchy of dictionnaries. We add a first generation (named as the
# study being done) to the root. This first generation is used set the initial particle
# distribution, and build a collider with only the optics set.
# ==================================================================================================

# Build empty tree: first generation (later added to the root), and second generation
children = {"base_collider": {"config_particles": {}, "config_mad": {}, "children": {}}}

# Add particles distribution parameters to the first generation
children["base_collider"]["config_particles"] = d_config_particles

# Add base machine parameters to the first generation
children["base_collider"]["config_mad"] = d_config_mad


# ==================================================================================================
# --- Complete tree for the simulations (generation 2)
#
# We now set a second generation for the tree. This second generation contains the tracking
# parameters, as well as a default set of parameters for the colliders (defined above), that we
# mutate according to the parameters we want to scan.
# ! Caution when mutating the dictionnary in this function, you have to pass a deepcopy to children,
# ! otherwise the dictionnary will be mutated for all the children.
# ==================================================================================================
track_array = np.arange(d_config_particles["n_split"])
for idx_job, (track, bunch_nb) in enumerate(itertools.product(track_array, l_bunch_to_scan)):
    # Mutate the appropriate collider parameters
    for beam in ["lhcb1", "lhcb2"]:
        d_config_collider["config_beambeam"]["mask_with_filling_pattern"]["i_bunch_b1"] = int(
            bunch_nb
        )

    # Complete the dictionnary for the tracking
    d_config_simulation["particle_file"] = f"../particles/{track:02}.parquet"
    d_config_simulation["collider_file"] = f"../collider/collider.json"

    # Add a child to the second generation, with all the parameters for the collider and tracking
    children["base_collider"]["children"][f"xtrack_{idx_job:04}"] = {
        "config_simulation": copy.deepcopy(d_config_simulation),
        "config_collider": copy.deepcopy(d_config_collider),
        "log_file": "tree_maker.log",
    }

# ==================================================================================================
# --- Simulation configuration
# ==================================================================================================
# Load the tree_maker simulation configuration
config = yaml.safe_load(open("config.yaml"))

# # Set the root children to the ones defined above
config["root"]["children"] = children

# Set miniconda environment path in the config
config["root"]["setup_env_script"] = os.getcwd() + "/../miniforge/bin/activate"

# ==================================================================================================
# --- Build tree and write it to the filesystem
# ==================================================================================================
# Define study name
study_name = "opt_flathv_75_1500_withBB_chroma5_eol_bbb_2228"

# Creade folder that will contain the tree
if not os.path.exists("scans/" + study_name):
    os.makedirs("scans/" + study_name)

# Move to the folder that will contain the tree
os.chdir("scans/" + study_name)

# Create tree object
start_time = time.time()
root = initialize(config)
print("Done with the tree creation.")
print("--- %s seconds ---" % (time.time() - start_time))

# From python objects we move the nodes to the filesystem.
start_time = time.time()
root.make_folders(generate_run_sh_htc)
print("The tree folders are ready.")
print("--- %s seconds ---" % (time.time() - start_time))

# Rename log files according to study
shutil.move("tree_maker.json", f"tree_maker_{study_name}.json")
shutil.move("tree_maker.log", f"tree_maker_{study_name}.log")