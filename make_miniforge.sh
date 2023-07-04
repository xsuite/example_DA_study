wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh
bash Miniforge3-Linux-x86_64.sh -b  -p ./miniforge -f
source miniforge/bin/activate
python -m pip install -r requirements.txt
mkdir modules
cd modules
git clone git@github.com:lhcopt/hllhc15.git
git clone -b release/v0.1.0 git@github.com:xsuite/tree_maker.git
python -m pip install -e tree_maker
git clone https://github.com/xsuite/xmask.git
pip install -e xmask
# git clone https://github.com/xsuite/xdeps.git
# pip install -e xdeps
cd ..
xsuite-prebuild
