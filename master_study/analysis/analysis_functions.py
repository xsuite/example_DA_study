import matplotlib
import matplotlib.pyplot as plt
import matplotlib_inline
import qrcode
import numpy as np
from scipy.ndimage.filters import gaussian_filter
import yaml
import shutil
import os


def apply_heatmap_style():
    plt.style.use("ggplot")
    matplotlib.rcParams["mathtext.fontset"] = "cm"
    matplotlib.rcParams["font.family"] = "STIXGeneral"
    # Not italized latex
    matplotlib.rcParams["mathtext.default"] = "regular"
    matplotlib.rcParams["font.weight"] = "light"
    matplotlib_inline.backend_inline.set_matplotlib_formats("retina")


# To add QR codes to plot
def add_QR_code(fig, link):
    # Add QR code pointing to the github repository
    qr = qrcode.QRCode(
        # version=None,
        box_size=10,
        border=1,
    )
    qr.add_data(link)
    qr.make(fit=False)
    im = qr.make_image(fill_color="black", back_color="transparent")
    newax = fig.add_axes([0.9, 0.9, 0.05, 0.05], anchor="NE", zorder=1)
    newax.imshow(im, resample=False, interpolation="none", filternorm=False)
    # Add link below qrcode
    newax.plot([0, 0], [0, 0], color="white", label="link")
    text = newax.annotate(
        "lin",
        xy=(0, 300),
        xytext=(0, 300),
        fontsize=30,
        url=link,
        bbox=dict(color="white", alpha=1e-6, url=link),
        alpha=0,
    )
    # Hide X and Y axes label marks
    newax.xaxis.set_tick_params(labelbottom=False)
    newax.yaxis.set_tick_params(labelleft=False)
    # Hide X and Y axes tick marks
    newax.set_xticks([])
    newax.set_yticks([])
    newax.set_axis_off()

    return fig


# Function to convert floats to scientific latex format
def latex_float(f):
    float_str = "{0:.2g}".format(f)
    if "e" in float_str:
        base, exponent = float_str.split("e")
        return r"${0} \times 10^{{{1}}}$".format(base, int(exponent))
    else:
        return float_str


def load_config(config_path):
    # Read configuration file
    with open(config_path, "r") as fid:
        config = yaml.safe_load(fid)
    return config


def get_title_from_conf(conf_mad, conf_collider):
    # LHC version
    LHC_version = conf_mad["links"]["acc-models-lhc"].split("modules/")[1]
    if LHC_version == "hllhc15":
        LHC_version = "HL-LHC v1.5"

    # Round or flat optics
    if "flatcc" in conf_mad["optics_file"]:
        optics = "Flat optics"
    else:
        optics = "Round optics"

    # Levelling
    if conf_collider["skip_leveling"]:
        levelling = "Start of levelling"
    else:
        levelling = "End of levelling"

    # Crab cavities
    if conf_collider["config_knobs_and_tuning"]["knob_settings"]["on_crab1"] is not None:
        crab_cavities = "CC ON"
    else:
        crab_cavities = "CC OFF"

    # Bunch number
    bunch_number_value = conf_collider["config_beambeam"]["mask_with_filling_pattern"]["i_bunch_b1"]
    bunch_number = f"Bunch {bunch_number_value}"

    # Bunch intensity
    bunch_intensity = (
        f"$N_b \simeq $"
        + latex_float(float(conf_collider["config_beambeam"]["num_particles_per_bunch"]))
        + "ppb"
    )

    # Beta star # ! Manually encoded for now
    if "flathv" in conf_mad["optics_file"]:
        bet1 = r"$\beta^{*}_{y,IP1}$"
        bet2 = r"$\beta^{*}_{x,IP1}$"
    elif "flatvh" in conf_mad["optics_file"]:
        bet1 = r"$\beta^{*}_{x,IP1}$"
        bet2 = r"$\beta^{*}_{y,IP1}$"
    if "75_180" in conf_mad["optics_file"]:
        beta = bet1 + r"$= 7.5$ cm, " + bet2 + r"$= 18$ cm"
    elif "500_1000" in conf_mad["optics_file"]:
        beta = bet1 + r"$= 0.5$ m, " + bet2 + r"$= 1$ m"
    else:
        raise ValueError("Optics configuration not automatized yet")

    # Crossing angle at IP1/5
    if "flathv" in conf_mad["optics_file"]:
        phi = r"$\Phi/2_{IP1(H)/5(V)}$"
    elif "flatvh" in conf_mad["optics_file"]:
        phi = r"$\Phi/2_{IP1(V)/5(H)}$"
    else:
        raise ValueError("Optics configuration not automatized yet")
    xing_value_IP15 = conf_collider["config_knobs_and_tuning"]["knob_settings"]["on_x1"]
    xing_IP15 = phi + f"$= {{{xing_value_IP15}}} \mu rad$"

    # Bunch length
    bunch_length_value = conf_collider["config_beambeam"]["sigma_z"] * 100
    bunch_length = f"$\sigma_{{z}} = {{{bunch_length_value}}}$ $cm$"

    # Crosing angle at IP8
    xing_value_IP8h = conf_collider["config_knobs_and_tuning"]["knob_settings"]["on_x8h"]
    xing_value_IP8v = conf_collider["config_knobs_and_tuning"]["knob_settings"]["on_x8v"]
    if xing_value_IP8v != 0 and xing_value_IP8h == 0:
        xing_IP8 = r"$\Phi/2_{IP8,V}$" + f"$= {{{xing_value_IP8v}}}$ $\mu rad$"
    elif xing_value_IP8v == 0 and xing_value_IP8h != 0:
        xing_IP8 = r"$\Phi/2_{IP8,H}$" + f"$= {{{xing_value_IP8h}}}$ $\mu rad$"
    else:
        raise ValueError("Optics configuration not automatized yet")

    # Normalized emittance
    emittance_value = round(conf_collider["config_beambeam"]["nemitt_x"] / 1e-6, 2)
    emittance = f"$\epsilon_{{n}} = {{{emittance_value}}}$ $\mu m$"

    # Chromaticity
    chroma_value = conf_collider["config_knobs_and_tuning"]["dqx"]["lhcb1"]
    chroma = r"$Q'$" + f"$= {{{chroma_value}}}$"

    # Intensity
    intensity_value = conf_collider["config_knobs_and_tuning"]["knob_settings"]["i_oct_b1"]
    intensity = f"$I_{{MO}} = {{{intensity_value}}}$ $A$"

    # Linear coupling
    coupling_value = conf_collider["config_knobs_and_tuning"]["delta_cmr"]
    coupling = f"$C^- = {{{coupling_value}}}$"

    # Filling scheme
    filling_scheme_value = conf_collider["config_beambeam"]["mask_with_filling_pattern"][
        "pattern_fname"
    ].split("filling_scheme/")[1]
    if "12inj" in filling_scheme_value:
        filling_scheme_value = filling_scheme_value.split("12inj")[0] + "12inj"
    filling_scheme = f"$F. Scheme:$ {filling_scheme_value}"
    title = (
        LHC_version
        + ". "
        + optics
        + ". "
        + levelling
        + ". "
        + crab_cavities
        + ". "
        + bunch_number
        + "."
        + "\n"
        + bunch_intensity
        + ", "
        + beta
        + ", "
        + xing_IP15
        + "\n"
        + bunch_length
        + ", "
        + xing_IP8
        + ", "
        + emittance
        + ", "
        + chroma
        + ", "
        + intensity
        + ", "
        + coupling
        + "\n"
        + filling_scheme
    )
    return title


def plot_heatmap(
    df_to_plot, study_name, link=None, plot_contours=True, conf_mad=None, conf_collider=None
):
    # Get numpy array from dataframe
    data_array = df_to_plot.to_numpy()

    # Define colormap and set NaNs to white
    cmap = matplotlib.cm.get_cmap("coolwarm_r", 50)
    cmap.set_bad("w")

    # Build heatmap, with inverted y axis
    fig, ax = plt.subplots()
    im = ax.imshow(data_array, cmap=cmap, vmin=3.5, vmax=8)
    ax.invert_yaxis()

    # Show all ticks and label them with the respective list entries
    ax.set_xticks(np.arange(len(df_to_plot.columns))[::2], labels=df_to_plot.columns[::2])
    ax.set_yticks(np.arange(len(df_to_plot.index))[::2], labels=df_to_plot.index[::2])

    # Loop over data dimensions and create text annotations.
    for i in range(len(df_to_plot.index)):
        for j in range(len(df_to_plot.columns)):
            text = ax.text(
                j, i, f"{data_array[i, j]:.1f}", ha="center", va="center", color="white", fontsize=4
            )

    # Smooth data for contours
    # make the matrix symmetric by replacing the lower triangle with the upper triangle
    data_smoothed = np.copy(data_array)
    data_smoothed[np.isnan(data_array)] = 0
    data_smoothed = data_smoothed + data_smoothed.T - np.diag(data_array.diagonal())
    data_smoothed = gaussian_filter(data_smoothed, 0.7)

    # Mask the lower triangle of the smoothed matrix
    mask = np.tri(data_smoothed.shape[0], k=-1)
    mx = np.ma.masked_array(data_smoothed, mask=mask.T)

    # Plot contours if requested
    if plot_contours:
        CSS = ax.contour(
            np.arange(0.5, data_array.shape[1]),
            np.arange(0.5, data_array.shape[0]),
            mx,
            colors="black",
            levels=list(np.arange(3, 6, 0.5)) + list(np.arange(6.5, 10, 0.5)),
            linewidths=0.2,
        )
        ax.clabel(CSS, inline=True, fontsize=6)
        CS2 = ax.contour(
            np.arange(0.5, data_array.shape[1]),
            np.arange(0.5, data_array.shape[0]),
            mx,
            colors="green",
            levels=[6],
            linewidths=1,
        )
        ax.clabel(CS2, inline=1, fontsize=6)

    # ! Diagonal lines must be plotted after the contour lines, because of bug in matplotlib
    # ! Careful, depending on how the tunes were defined, may be shifted by 1
    # Diagonal lines
    ax.plot([0, 1000], [1, 1001], color="tab:blue", linestyle="--", linewidth=1)
    ax.plot([0, 1000], [-9, 991], color="tab:blue", linestyle="--", linewidth=1)
    ax.plot([0, 1000], [-4, 996], color="black", linestyle="--", linewidth=1)

    # Define title and axis labels
    if conf_mad is not None and conf_collider is not None:
        ax.set_title(
            get_title_from_conf(conf_mad, conf_collider),
            fontsize=10,
        )
    ax.set_xlabel("Horizontal tune " + r"$Q_x$")
    ax.set_ylabel("Vertical tune " + r"$Q_y$")
    ax.set_xlim(0 - 0.5, data_array.shape[1] - 0.5)
    ax.set_ylim(0 - 0.5, data_array.shape[0] - 0.5)

    # Ticks on top
    ax.xaxis.tick_top()
    # Rotate the tick labels and set their alignment.
    plt.setp(ax.get_xticklabels(), rotation=-30, ha="right", rotation_mode="anchor")

    # Create colorbar
    cbar = ax.figure.colorbar(im, ax=ax, fraction=0.026, pad=0.04)
    cbar.ax.set_ylabel("Minimum DA (" + r"$\sigma$" + ")", rotation=90, va="bottom", labelpad=15)
    plt.grid(visible=None)

    # Add QR code
    if link is not None:
        fig = add_QR_code(fig, link)

    plt.savefig("plots/output_" + study_name + ".pdf", bbox_inches="tight")
    plt.show()


def copy_study_on_eos(study_name, type_analysis="tune_scan"):
    path_study = "/afs/cern.ch/work/c/cdroin/private/example_DA_study/master_study/"
    path_EOS = "/eos/home-c/cdroin/save_simulations/"
    path_archive = path_EOS + study_name + "/"

    ### Rebuild structue of the study on EOS
    try:
        os.mkdir(path_archive)
    except FileExistsError:
        print("Directory already exists, continue...")

    # # Copy all master jobs
    # shutil.copytree(path_study + "master_jobs",
    #                 path_archive + "master_jobs",
    #                 dirs_exist_ok=True)

    # Copy analysis
    suffix_analysis = f"analysis/{type_analysis}/analysis_" + study_name + ".ipynb"
    path_source_analysis = path_study + suffix_analysis
    path_destination_analysis = path_archive + suffix_analysis
    os.makedirs(os.path.dirname(path_destination_analysis), exist_ok=True)
    shutil.copy(path_source_analysis, path_destination_analysis)

    # Copy scripts to generate and analyse the scan
    suffix_scripts = [
        "001_make_folders_" + study_name + ".py",
    ]
    #  "002_chronjob.py",
    #  "003_postprocessing.py"]
    for suffix in suffix_scripts:
        path_source = path_study + suffix
        path_destination = path_archive + suffix
        shutil.copy(path_source, path_destination)

    # Copy scan
    print("Start copying scan, this may take a while...")
    shutil.copytree(
        path_study + "scans/" + study_name,
        path_archive + "/scans/" + study_name,
        dirs_exist_ok=True,
    )

    return path_archive, path_EOS


def archive_and_clean(path_archive, path_EOS):
    # Convert the archive to a zip file, and export to EOS
    shutil.make_archive(path_archive, "zip", path_EOS, path_archive.split("/")[-1])

    # Delete the folder archive
    shutil.rmtree(path_archive)