import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import matplotlib.patches as patches
import np_tif
from stack_registration import bucket

def main():
    assert os.path.isdir('./../images')
    if not os.path.isdir('./../images/figure_5'):
        os.mkdir('./../images/figure_5')

    num_delays = 3
    image_h = 128
    image_w = 380

    # power calibration:
    # for a given voltage input to the AOM, how many milliwatts do we
    # expect the AOM to output
    green_max_mW = 130 # measured with power meter before sample
    # When the experiment is run, the acquisition code sends voltages to
    # the AOM via the analog out card. The maximum voltage is the same
    # as was used to deliver the max power to the power meter (see
    # previous line). We replaced the green filter with neutral density
    # filters and measured green power on the camera while running the
    # same acquisition code used to take the fluorescence data.
    green_powers = np.array(
        (123,296,574,926,1591,2666,3815)) # units: camera counts
    camera_background_counts = 100
    green_powers = green_powers - camera_background_counts
    green_powers = green_powers * green_max_mW / max(green_powers) # units: mW

    red_max_mW = 230 # measured with power meter before sample
    red_powers = np.array((0, red_max_mW))

    data = np_tif.tif_to_array(
        './../../stimulated_emission_imaging-data' +
        '/2018_03_05_STE_depletion_orange_bead_15_low_power' +
        '/dataset_green_all_powers_up.tif').astype(np.float64)

    # get rid of overexposed rows at top and bottom of images
    less_rows = 3
    data = data[:,0+less_rows:data.shape[1]-less_rows,:]

    # reshape to hyperstack
    data = data.reshape((
        len(green_powers),
        num_delays,
        data.shape[1],
        data.shape[2],
        ))

    # fluorescence image (no STE depletion) stack: the average between
    # max negative and positive red/green pulse delay images
    fluorescence_stack = 0.5 * (data[:,0,:,:] + data[:,2,:,:])
    fluorescence_stack_green_early = data[:,2,:,:]
    # fluorescence image (with STE depletion) stack
    depleted_stack = data[:,1,:,:] # zero red/green delay

    # get background signal level
    top_bg = 10
    bot_bg = 20
    left_bg = 10
    right_bg = 20
    fluorescence_signal_bg = (
        fluorescence_stack[:,top_bg:bot_bg,left_bg:right_bg
                           ].mean(axis=2).mean(axis=1)
        )
    fluorescence_signal_bg_green_early = (
        fluorescence_stack_green_early[:,top_bg:bot_bg,left_bg:right_bg
                                       ].mean(axis=2).mean(axis=1)
        )
    depleted_signal_bg = (
        depleted_stack[:,top_bg:bot_bg,left_bg:right_bg
                       ].mean(axis=2).mean(axis=1)
        )

    # crop, bg subtract, and downsample brightest fluorescence image to
    # include on the saturation plot as an inset
    top = 0
    bot = top + 112
    left = 152
    right = left + 130
    fluorescence_cropped = (fluorescence_stack_green_early[-1, top:bot, left:right] -
                            fluorescence_signal_bg_green_early[-1])
    fluorescence_cropped = bucket(fluorescence_cropped, bucket_size=(8, 8))
    fluorescence_cropped[-2:-1, 1:6] = np.max(fluorescence_cropped) # scale bar
    
    # average points around center lobe of the fluorescence image to get
    # "average signal level" for darkfield and STE images
    top = 29
    bot = top + 48
    left = 190
    right = left + 48
    fluorescence_signal = (
        fluorescence_stack[:, top:bot, left:right].mean(axis=2).mean(axis=1))
    fluorescence_signal = fluorescence_signal - fluorescence_signal_bg
    depleted_signal = (
        depleted_stack[:, top:bot, left:right].mean(axis=2).mean(axis=1))
    depleted_signal = depleted_signal - depleted_signal_bg

    # IMPORTANT PARAMETERS FOR FIT
    brightness = 142#97
    mW_per_kex = 37#80
    mW_per_kdep = 5000#10000

    # equally spaced fluorophore alignment angles (wrt laser polarization)
    K = 400 # number of angles to try
    theta = np.linspace(0, np.pi, K)
    N = K - 1 #number of spaces between angles

    #population weight for each angle
    #norm = normalization factor for summation over theta
    #(phi not necessary due to symmetry)
    norm = np.pi / 2 / N
    n2_weight = np.sin(theta) * norm

    sigma_weight = (np.cos(theta))**2# cross section weight for each angle

    # finely sample green powers
    green_powers_fine = np.linspace(green_powers[0], green_powers[-1], 100)

    # initiate array that contains model fluorescence v. green at every angle
    model_fl_all = np.zeros(
        (theta.shape[0], green_powers_fine.shape[0]))
    model_fl_max_all = np.zeros(
        (theta.shape[0], green_powers_fine.shape[0]))
    model_fl_min_all = np.zeros(
        (theta.shape[0], green_powers_fine.shape[0]))
    model_fl_dep_all = np.zeros(
        (theta.shape[0], green_powers_fine.shape[0]))
    model_fl_dep_max_all = np.zeros(
        (theta.shape[0], green_powers_fine.shape[0]))
    model_fl_dep_min_all = np.zeros(
        (theta.shape[0], green_powers_fine.shape[0]))

    # compute model fluorescence for each angle
    for theta_index in range(N):
        n2 = n2_weight[theta_index]
        sigma = sigma_weight[theta_index]

        # compute rate constants
        kex = green_powers_fine / mW_per_kex * sigma
        kex_min = 1/(1/kex * 0.93)
        kex_max = 1/(1/kex * 1.07)
        kdep = red_powers[-1] / mW_per_kdep * sigma
        kdep_min = 1/(1/kdep * 0.6)
        kdep_max = 1/(1/kdep * 1.4)

        # predict fluorescence
        model_fl = kex / (1 + kex) * n2
        model_fl_all[theta_index, :] = model_fl
        model_fl_max = kex_max / (1 + kex_max) * n2
        model_fl_max_all[theta_index, :] = model_fl_max
        model_fl_min = kex_min / (1 + kex_min) * n2
        model_fl_min_all[theta_index, :] = model_fl_min
        # predict depleted fluorescence
        model_fl_dep = kex / (1 + kex + kdep) * n2
        model_fl_dep_all[theta_index, :] = model_fl_dep
        model_fl_dep_max = kex / (1 + kex + kdep_max) * n2
        model_fl_dep_max_all[theta_index, :] = model_fl_dep_max
        model_fl_dep_min = kex / (1 + kex + kdep_min) * n2
        model_fl_dep_min_all[theta_index, :] = model_fl_dep_min

    # sum weighted fluorescence over all angles
    model_fl = model_fl_all.sum(axis=0)
    model_fl_max = model_fl_max_all.sum(axis=0)
    model_fl_min = model_fl_min_all.sum(axis=0)
    model_fl_dep = model_fl_dep_all.sum(axis=0)
    model_fl_dep_max = model_fl_dep_max_all.sum(axis=0)
    model_fl_dep_min = model_fl_dep_min_all.sum(axis=0)
    
    fig = plt.figure()
    ax1 = fig.add_subplot(1,1,1)
    ax1.plot(green_powers_fine, model_fl * brightness, '-',
             label=r'Model, $h_{stim}\sigma_{23}=0$', color='green')
    ax1.fill_between(green_powers_fine,
                     model_fl_max * brightness,
                     model_fl_min * brightness,
                     color="#C0FFC0")
    dep_mult = ("{:.3f}".format(kdep))
    ax1.plot(green_powers_fine, model_fl_dep * brightness, '-',
             label=(r'Model, $h_{stim}\sigma_{23}=' +
                    dep_mult + r'(1/\tau_{exc})$'),
             color='red')
    ax1.fill_between(green_powers_fine,
                     model_fl_dep_max * brightness,
                     model_fl_dep_min * brightness,
                     color='#FFD0D0')
    plt.ylabel('Average pixel brightness (sCMOS counts)', fontsize=15)
    ax1.plot(green_powers,fluorescence_signal, 'o',
             label='Measured, no depletion', color='green')
    ax1.plot(green_powers,depleted_signal, 'o',
             label='Measured, with depletion (230 mW)', color='red')
    ax1.set_xlabel('Excitation power (mW)',fontsize=16)
    plt.axis([0, 140, 0, 73])
    leg = plt.legend(loc='lower right' ,title='Fluorescence', fontsize=14)
    plt.setp(leg.get_title(), fontsize=15)
    plt.grid()
    ax2 = ax1.twiny()
    formatter = FuncFormatter(
        lambda green_powers, pos: '{:0.2f}'.format(green_powers/mW_per_kex))
    ax2.xaxis.set_major_formatter(formatter)
    ax2.set_xlim(ax1.get_xlim())
    ax2.set_xlabel(r'$h_{exc}\sigma_{01}/(1/\tau_{exc})$', fontsize=17)
    ax2 = ax1.twinx()
    formatter = FuncFormatter(
        lambda model_fl, pos: '{:0.2f}'.format(model_fl/brightness))
    ax2.yaxis.set_major_formatter(formatter)
    ax2.set_ylim(ax1.get_ylim())
    ax2.set_ylabel(r'Orientation-averaged excitation fraction $\bar n_2$',
                   fontsize=17)
    
    a = plt.axes([0.17, 0.6, .25, .25])
    plt.imshow(fluorescence_cropped, cmap=plt.cm.gray, interpolation='nearest')
    plt.xticks([])
    plt.yticks([])
    a.text(0.9, 1.5, 'Orange bead',
           fontsize=14, color='white', fontweight='bold')
    rect = patches.Rectangle(
        (4.6, 2.9), 6, 6,
        linewidth=1, linestyle='dashed', edgecolor='y', facecolor='none')
    a.add_patch(rect)
    plt.savefig(
        './../images/figure_5/fluorescence_depletion_orange_dye_brightness_optimal.svg')
    plt.show()

    # change brightness * 1.5 and scale rate constant to fit
    brightness_hi = brightness * 1.5
    rate_const_mod = 1.91
    extra_kdep_mod = 0.7
    
    # modify rate constants to fit new brightness
    mW_per_kex_hi = mW_per_kex * rate_const_mod
    mW_per_kdep_hi = mW_per_kdep * rate_const_mod * extra_kdep_mod

    # compute model fluorescence for each angle
    for theta_index in range(N):
        n2 = n2_weight[theta_index]
        sigma = sigma_weight[theta_index]

        # compute rate constants
        kex = green_powers_fine / mW_per_kex_hi * sigma
        kex_min = 1/(1/kex * 0.93)
        kex_max = 1/(1/kex * 1.07)
        kdep = red_powers[-1] / mW_per_kdep_hi * sigma
        kdep_min = 1/(1/kdep * 0.6)
        kdep_max = 1/(1/kdep * 1.4)

        # predict fluorescence
        model_fl = kex / (1 + kex) * n2
        model_fl_all[theta_index, :] = model_fl
        model_fl_max = kex_max / (1 + kex_max) * n2
        model_fl_max_all[theta_index, :] = model_fl_max
        model_fl_min = kex_min / (1 + kex_min) * n2
        model_fl_min_all[theta_index, :] = model_fl_min
        # predict depleted fluorescence
        model_fl_dep = kex / (1 + kex + kdep) * n2
        model_fl_dep_all[theta_index, :] = model_fl_dep
        model_fl_dep_max = kex / (1 + kex + kdep_max) * n2
        model_fl_dep_max_all[theta_index, :] = model_fl_dep_max
        model_fl_dep_min = kex / (1 + kex + kdep_min) * n2
        model_fl_dep_min_all[theta_index, :] = model_fl_dep_min

    # sum weighted fluorescence over all angles
    model_fl = model_fl_all.sum(axis=0)
    model_fl_max = model_fl_max_all.sum(axis=0)
    model_fl_min = model_fl_min_all.sum(axis=0)
    model_fl_dep = model_fl_dep_all.sum(axis=0)
    model_fl_dep_max = model_fl_dep_max_all.sum(axis=0)
    model_fl_dep_min = model_fl_dep_min_all.sum(axis=0)
    
    fig = plt.figure()
    ax1 = fig.add_subplot(1, 1, 1)
    ax1.plot(green_powers_fine, model_fl * brightness_hi, '-',
             label=r'Model, $h_{stim}\sigma_{23}=0$', color='green')
    ax1.fill_between(green_powers_fine,
                     model_fl_max * brightness_hi,
                     model_fl_min * brightness_hi,
                     color="#C0FFC0")
    dep_mult = ("{:.3f}".format(kdep))
    ax1.plot(green_powers_fine, model_fl_dep * brightness_hi, '-',
             label=(
                 r'Model, $h_{stim}\sigma_{23}=' +
                 dep_mult + r'(1/\tau_{exc})$'),
             color='red')
    ax1.fill_between(green_powers_fine,
                     model_fl_dep_max * brightness_hi,
                     model_fl_dep_min * brightness_hi,
                     color='#FFD0D0')
    plt.ylabel('Average pixel brightness (sCMOS counts)', fontsize=15)
    ax1.plot(green_powers,fluorescence_signal, 'o',
             label='Measured, no depletion', color='green')
    ax1.plot(green_powers,depleted_signal, 'o',
             label='Measured, with depletion (230 mW)', color='red')
    ax1.set_xlabel('Excitation power (mW)',fontsize=16)
    plt.axis([0, 140, 0, 73])
    leg = plt.legend(loc='lower right', title='Fluorescence', fontsize=14)
    plt.setp(leg.get_title(), fontsize=15)
    plt.grid()
    ax2 = ax1.twiny()
    formatter = FuncFormatter(
        lambda green_powers, pos: '{:0.2f}'.format(green_powers/mW_per_kex))
    ax2.xaxis.set_major_formatter(formatter)
    ax2.set_xlim(ax1.get_xlim())
    ax2.set_xlabel(r'$h_{exc}\sigma_{01}/(1/\tau_{exc})$', fontsize=17)
    ax2 = ax1.twinx()
    formatter = FuncFormatter(
        lambda model_fl, pos: '{:0.2f}'.format(model_fl/brightness_hi))
    ax2.yaxis.set_major_formatter(formatter)
    ax2.set_ylim(ax1.get_ylim())
    ax2.set_ylabel(r'Orientation-averaged excitation fraction $\bar n_2$',
                   fontsize=17)
    
    a = plt.axes([0.17, 0.6, .25, .25])
    plt.imshow(fluorescence_cropped, cmap=plt.cm.gray, interpolation='nearest')
    plt.xticks([])
    plt.yticks([])
    a.text(0.9, 1.5, 'Orange bead',
           fontsize=14, color='white', fontweight='bold')
    rect = patches.Rectangle(
        (4.6, 2.9), 6, 6,
        linewidth=1, linestyle='dashed', edgecolor='y', facecolor='none')
    a.add_patch(rect)
    plt.savefig(
        './../images/figure_5/fluorescence_depletion_orange_dye_brightness_hi.svg')
    plt.show()





    # change brightness / 1.5 and scale rate constant to fit
    brightness_lo = brightness / 1.5
    rate_const_mod = 2.3
    extra_kdep_mod = 0.6
    
    # modify rate constants to fit new brightness
    mW_per_kex_lo = mW_per_kex / rate_const_mod
    mW_per_kdep_lo = mW_per_kdep / rate_const_mod / extra_kdep_mod

    # compute model fluorescence for each angle
    for theta_index in range(N):
        n2 = n2_weight[theta_index]
        sigma = sigma_weight[theta_index]

        # compute rate constants
        kex = green_powers_fine / mW_per_kex_lo * sigma
        kex_min = 1/(1/kex * 0.93)
        kex_max = 1/(1/kex * 1.07)
        kdep = red_powers[-1] / mW_per_kdep_lo * sigma
        kdep_min = 1/(1/kdep * 0.6)
        kdep_max = 1/(1/kdep * 1.4)

        # predict fluorescence
        model_fl = kex / (1 + kex) * n2
        model_fl_all[theta_index, :] = model_fl
        model_fl_max = kex_max / (1 + kex_max) * n2
        model_fl_max_all[theta_index, :] = model_fl_max
        model_fl_min = kex_min / (1 + kex_min) * n2
        model_fl_min_all[theta_index, :] = model_fl_min
        # predict depleted fluorescence
        model_fl_dep = kex / (1 + kex + kdep) * n2
        model_fl_dep_all[theta_index, :] = model_fl_dep
        model_fl_dep_max = kex / (1 + kex + kdep_max) * n2
        model_fl_dep_max_all[theta_index, :] = model_fl_dep_max
        model_fl_dep_min = kex / (1 + kex + kdep_min) * n2
        model_fl_dep_min_all[theta_index, :] = model_fl_dep_min

    # sum weighted fluorescence over all angles
    model_fl = model_fl_all.sum(axis=0)
    model_fl_max = model_fl_max_all.sum(axis=0)
    model_fl_min = model_fl_min_all.sum(axis=0)
    model_fl_dep = model_fl_dep_all.sum(axis=0)
    model_fl_dep_max = model_fl_dep_max_all.sum(axis=0)
    model_fl_dep_min = model_fl_dep_min_all.sum(axis=0)
    
    fig = plt.figure()
    ax1 = fig.add_subplot(1, 1, 1)
    ax1.plot(green_powers_fine, model_fl * brightness_lo, '-',
             label=r'Model, $h_{stim}\sigma_{23}=0$', color='green')
    ax1.fill_between(green_powers_fine,
                     model_fl_max * brightness_lo,
                     model_fl_min * brightness_lo,
                     color="#C0FFC0")
    dep_mult = ("{:.3f}".format(kdep))
    ax1.plot(green_powers_fine, model_fl_dep * brightness_lo, '-',
             label=(r'Model, $h_{stim}\sigma_{23}=' +
                    dep_mult + r'(1/\tau_{exc})$'),
             color='red')
    ax1.fill_between(green_powers_fine,
                     model_fl_dep_max * brightness_lo,
                     model_fl_dep_min * brightness_lo,
                     color='#FFD0D0')
    plt.ylabel('Average pixel brightness (sCMOS counts)',fontsize=15)
    ax1.plot(green_powers,fluorescence_signal, 'o',
             label='Measured, no depletion', color='green')
    ax1.plot(green_powers,depleted_signal, 'o',
             label='Measured, with depletion (230 mW)', color='red')
    ax1.set_xlabel('Excitation power (mW)', fontsize=16)
    plt.axis([0, 140, 0, 73])
    leg = plt.legend(loc='lower right', title='Fluorescence', fontsize=14)
    plt.setp(leg.get_title(), fontsize=15)
    plt.grid()
    ax2 = ax1.twiny()
    formatter = FuncFormatter(
        lambda green_powers, pos: '{:0.2f}'.format(green_powers/mW_per_kex))
    ax2.xaxis.set_major_formatter(formatter)
    ax2.set_xlim(ax1.get_xlim())
    ax2.set_xlabel(r'$h_{exc}\sigma_{01}/(1/\tau_{exc})$', fontsize=17)
    ax2 = ax1.twinx()
    formatter = FuncFormatter(
        lambda model_fl, pos: '{:0.2f}'.format(model_fl/brightness_lo))
    ax2.yaxis.set_major_formatter(formatter)
    ax2.set_ylim(ax1.get_ylim())
    ax2.set_ylabel(r'Orientation-averaged excitation fraction $\bar n_2$',
                   fontsize=17)
    
    a = plt.axes([0.17, 0.6, .25, .25])
    plt.imshow(fluorescence_cropped, cmap=plt.cm.gray, interpolation='nearest')
    plt.xticks([])
    plt.yticks([])
    a.text(0.9, 1.5, 'Orange bead',
           fontsize=14, color='white', fontweight='bold')
    rect = patches.Rectangle(
        (4.6, 2.9), 6, 6,
        linewidth=1, linestyle='dashed', edgecolor='y', facecolor='none')
    a.add_patch(rect)
    plt.savefig(
        './../images/figure_5/fluorescence_depletion_orange_dye_brightness_lo.svg')
    plt.show()


    return None




def annular_filter(x, r1, r2):
    assert r2 > r1 >= 0

    x_ft = np.fft.fftn(x)
    n_y, n_x = x.shape[-2:]
    kx = np.fft.fftfreq(n_x).reshape(1, 1, n_x)
    ky = np.fft.fftfreq(n_y).reshape(1, n_y, 1)

    x_ft[kx**2 + ky**2 > r2**2] = 0
    x_ft[kx**2 + ky**2 < r1**2] = 0

    x_filtered = np.fft.ifftn(x_ft).real

    return x_filtered

if __name__ == '__main__':
    main()
