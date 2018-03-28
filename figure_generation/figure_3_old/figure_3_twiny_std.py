import os
import numpy as np
import np_tif
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import matplotlib.patches as patches

def main():
    w_shift = -19
    h_shift = 17

    # the data to be plotted by this program is generated from raw tifs
    # and repetition_average_expt_and_control.py

    assert os.path.isdir('./../images')
    if not os.path.isdir('./../images/figure_3'):
        os.mkdir('./../images/figure_3')

    num_reps = 10 # number of times a power/delay stack was taken
    num_delays = 5
    image_h = 128
    image_w = 380

    # power calibration
    # red max power is 300 mW
    # green max power is 1450 mW
    # green powers calibrated using camera
    green_max_mW = 1450
    green_powers = np.array(
        (113.9,119.6,124.5,135,145.5,159.5,175.3,193.1,234.5,272.2,334.1,385.7,446.1))
    green_powers = green_powers - min(green_powers)
    green_powers = green_powers * green_max_mW / max(green_powers)
    green_powers = np.around(green_powers).astype(int)

    # red powers calibrated using camera
    red_bg = 26.6
    red_max_mW = 300
    red_powers = np.array(
        (26.6, 113, 198, 276, 353, 438, 537))
    red_powers -= red_bg
    red_powers = red_powers * red_max_mW / max(red_powers)
    red_powers = np.around(red_powers).astype(int)

    filename = (
        './../../stimulated_emission_data/figure_3/dataset_registered_avg.tif')
    data = np_tif.tif_to_array(filename).astype(np.float64)
    std_filename = (
        './../../stimulated_emission_data/figure_3/std_dev_registered.tif')
    std = np_tif.tif_to_array(std_filename).astype(np.float64)

    # get rid of overexposed rows at top and bottom of images
    less_rows = 3
    data = data[:,0+less_rows:data.shape[1]-less_rows,:]
    std = std[:,0+less_rows:data.shape[1]-less_rows,:]
    
    # reshape to hyperstack
    data = data.reshape((
        len(red_powers),
        len(green_powers),
        num_delays,
        data.shape[1],
        data.shape[2],
        ))
    std = std.reshape((
        len(red_powers),
        len(green_powers),
        num_delays,
        std.shape[1],
        std.shape[2],
        ))


    # from the image where red/green are simultaneous, subtract the
    # average of images taken when the delay magnitude is greatest
    depletion_stack = (
        data[:,:,2,:,:] - # zero red/green delay
        0.5 * (data[:,:,0,:,:] + data[:,:,4,:,:]) # max red/green delay
##        data[:,:,0,:,:] # max red/green delay
        )

    # fluorescence image (no STE) stack
    fluorescence_stack = 0.5 * (data[:,:,0,:,:] + data[:,:,4,:,:])
    depleted_stack = data[:,:,2,:,:] # zero red/green delay
    std_fluorescence_stack = 0.5 * (std[:,:,0,:,:] + std[:,:,4,:,:])
    std_depleted_stack = std[:,:,2,:,:] # zero red/green delay

    # save processed stacks
##    tif_shape = (
##        len(red_powers)*len(green_powers),
##        depletion_stack.shape[2],
##        depletion_stack.shape[3],
##        )
##    np_tif.array_to_tif(
##        depletion_stack.reshape(tif_shape),'depletion_stack.tif')
##    np_tif.array_to_tif(
##        fluorescence_stack.reshape(tif_shape),'fluorescence_stack.tif')
##    np_tif.array_to_tif(
##        depleted_stack.reshape(tif_shape),'depleted_stack_ctrl.tif')

    # plot darkfield and stim emission signal
    # get background signal level for brightest image
    top_bg = 20
    bot_bg = 30
    left_bg = 20
    right_bg = 30
    fluorescence_signal_bg = (
        fluorescence_stack[:,:,top_bg:bot_bg,left_bg:right_bg
                           ].mean(axis=3).mean(axis=2)
        )
    depleted_signal_bg = (
        depleted_stack[:,:,top_bg:bot_bg,left_bg:right_bg
                       ].mean(axis=3).mean(axis=2)
        )
    std_fluorescence_signal_bg = (
        std_fluorescence_stack[:,:,top_bg:bot_bg,left_bg:right_bg
                           ].mean(axis=3).mean(axis=2)
        )
    std_depleted_signal_bg = (
        std_depleted_stack[:,:,top_bg:bot_bg,left_bg:right_bg
                       ].mean(axis=3).mean(axis=2)
        )

    # crop, bg subtract, and spatially filter image
    top = 0 + h_shift
    bot = 112 + h_shift
    left = 122 + w_shift
    right = 249 + w_shift
    fluorescence_cropped = (fluorescence_stack[-1,-1,top:bot,left:right] -
                            fluorescence_signal_bg[-1,-1])
    fluorescence_cropped = fluorescence_cropped.reshape(
        1,fluorescence_cropped.shape[0],fluorescence_cropped.shape[1])
    fluorescence_cropped = annular_filter(fluorescence_cropped,r1=0,r2=0.03)
    fluorescence_cropped = fluorescence_cropped[0,:,:]
    depletion_cropped = depletion_stack[-1,-1,top:bot,left:right]
    depletion_cropped = depletion_cropped.reshape(
        1,depletion_cropped.shape[0],depletion_cropped.shape[1])
    depletion_cropped = annular_filter(depletion_cropped,r1=0,r2=0.03)
    depletion_cropped = depletion_cropped[0,:,:]
    fluorescence_cropped[101:107,5:34] = 200 # scale bar
    depletion_cropped[101:107,5:34] = -20 # scale bar

##    fig, (ax0, ax1) = plt.subplots(nrows=1,ncols=2,figsize=(16,5))
##
##    cax0 = ax0.imshow(fluorescence_cropped, cmap=plt.cm.gray)
##    ax0.axis('off')
##    cbar0 = fig.colorbar(cax0, ax = ax0)
##    ax0.set_title('Fluorescence image of nanodiamond')
##
##    cax1 = ax1.imshow(depletion_cropped, cmap=plt.cm.gray)
##    cbar1 = fig.colorbar(cax1, ax = ax1)
##    ax1.set_title('Fluorescence intensity decreased due to stim. emission')
##    ax1.axis('off')
##    plt.savefig('./../images/figure_3/fluorescence_depletion_image.svg')
    
    # average points around center lobe of the nanodiamond image to get
    # "average signal level" for darkfield and STE images
    top = 31 + h_shift
    bot = 84 + h_shift
    left = 160 + w_shift
    right = 215 + w_shift
    depletion_signal = (
        depletion_stack[:,:,top:bot,left:right].mean(axis=3).mean(axis=2))
    depleted_signal = (
        depleted_stack[:,:,top:bot,left:right].mean(axis=3).mean(axis=2))
    depleted_signal = depleted_signal - depleted_signal_bg
    fluorescence_signal = (
        fluorescence_stack[:,:,top:bot,left:right].mean(axis=3).mean(axis=2))
    fluorescence_signal = fluorescence_signal - fluorescence_signal_bg
    # for std deviation too
    std_depleted_signal = (
        std_depleted_stack[:,:,top:bot,left:right].mean(axis=3).mean(axis=2))
##    std_depleted_signal = std_depleted_signal - std_depleted_signal_bg
    std_fluorescence_signal = (
        std_fluorescence_stack[:,:,top:bot,left:right].mean(axis=3).mean(axis=2))
##    std_fluorescence_signal = std_fluorescence_signal - std_fluorescence_signal_bg

##    np_tif.array_to_tif(STE_signal,'STE_signal_array.tif')
##    np_tif.array_to_tif(crosstalk_signal,'crosstalk_signal_array.tif')
##    np_tif.array_to_tif(darkfield_signal,'darkfield_signal_array.tif')
    
    # plot signal
##    mW_per_kex = 950
    mW_per_kex = 930
    kex = green_powers / mW_per_kex
    kex_min = 1.1*kex
    kex_max = 0.9*kex

##    mW_per_kdep = 950
    mW_per_kdep = 930
    kdep = red_powers[-1] / mW_per_kdep
    kdep_min = 0.6*kdep
    kdep_max = 1.4*kdep

    brightness = 120
    model_fl = kex / (1 + kex)
    model_fl_max = kex_max / (1 + kex_max)
    model_fl_min = kex_min / (1 + kex_min)
    model_fl_dep = kex / (1 + kex + kdep)
##    model_fl_dep_max = kex / (1 + kex + kdep_max)
##    model_fl_dep_min = kex / (1 + kex + kdep_min)
    model_fl_dep_max = kex_max / (1 + kex_max + kdep)
    model_fl_dep_min = kex_min / (1 + kex_min + kdep)

    nd_brightness = depleted_signal[0,:]/brightness
    nd_brightness_depleted = depleted_signal[-1,:]/brightness
    nd_brightness_std = std_depleted_signal[0,:]/brightness
    nd_brightness_depleted_std = std_depleted_signal[-1,:]/brightness
    
    fig = plt.figure()
    ax1 = fig.add_subplot(1,1,1)
    ax1.errorbar(green_powers,nd_brightness,yerr=nd_brightness_std,fmt='o',linewidth=3,capthick=2,
             label='Measured, 0 mW stimulation', color='green')
    ax1.errorbar(green_powers,nd_brightness_depleted,yerr=nd_brightness_depleted_std,fmt='o',
             label='Measured, 300 mW stimulation', color='red')
    ax1.set_xlabel('Excitation power (mW)',fontsize=16)
##    ax1.plot(green_powers, model_fl, '-',
##             label='Nanodiamond fluorescence (model)', color='green')
##    ax1.plot(green_powers, model_fl_dep, '-',
##             label='Depleted nanodiamond fluorescence (model)', color='red')
    ax1.plot(green_powers, model_fl, '-',
             label=r'Model, $h_{stim}\sigma_{23}=0$', color='green')
##    ax1.fill_between(green_powers, model_fl_max, model_fl_min,color='honeydew')
    ax1.fill_between(green_powers, model_fl_max, model_fl_min,color="#C0FFC0")
    ax1.plot(green_powers, model_fl_dep, '-',
             label=r'Model, $h_{stim}\sigma_{23}=0.3(1/\tau_{fluor})$', color='red')
##    ax1.plot(green_powers, model_fl_dep_max, '-',color='red')
##    ax1.plot(green_powers, model_fl_dep_min, '-',color='red')
    ax1.fill_between(green_powers, model_fl_dep_max, model_fl_dep_min,color='#FFD0D0')
    plt.ylabel(r'Excitation fraction $n_2$',fontsize=17)
    plt.axis([0,1600,0,0.7])
    leg = plt.legend(loc='lower right',title='Fluorescence',fontsize=14)
    plt.setp(leg.get_title(),fontsize=15)
    plt.grid()
    ax2 = ax1.twiny()
    formatter = FuncFormatter(
        lambda green_powers, pos: '{:0.1f}'.format(green_powers/mW_per_kex))
    ax2.xaxis.set_major_formatter(formatter)
    ax2.set_xlim(ax1.get_xlim())
##    ax2.set_xlabel('k_ex = excitation power (mW) / %i\n'%(mW_per_kex))
    ax2.set_xlabel(r'$h_{exc}\sigma_{01}/(1/\tau_{fluor})$',fontsize=17)
    ax2 = ax1.twinx()
    ax2.set_yticks(np.round(np.linspace(0,0.7,num=8)*brightness))
    ax2.set_ylabel('Average pixel brightness (sCMOS counts)',fontsize=15)
##    plt.title("k_ex  = mW/%i\n"%(mW_per_kex) + "k_dep = mW/%i"%(mW_per_kdep))
    a = plt.axes([0.17, 0.6, .25, .25])
    plt.imshow(fluorescence_cropped, cmap=plt.cm.gray)
    plt.xticks([])
    plt.yticks([])
    a.text(8,15,'Nanodiamond',fontsize=14,color='white',fontweight='bold')
    rect = patches.Rectangle(
        (39,29),55,53,linewidth=2,linestyle='dashed',edgecolor='y',facecolor='none')
    a.add_patch(rect)
    plt.savefig('./../images/figure_3/fluorescence_depletion_nd.svg')
    plt.show()
    

##    plt.figure()
##    for (pow_num,rd_pow) in enumerate(red_powers):
##        plt.plot(
##            green_powers,depleted_signal[pow_num,:],
##            '.-',label=('Red power = '+str(rd_pow)+' mW'))
##    plt.title('Average fluorescence signal in main lobe')
##    plt.xlabel('Green power (mW)')
##    plt.ylabel('Fluorescence light signal (CMOS pixel counts)')
##    plt.legend(loc='lower right')
##    plt.ylim(0,80)
##    plt.grid()
####    plt.savefig('./../images/figure_4/fluorescence_v_green_power.svg')    
##    
##    plt.figure()
##    for (pow_num,gr_pow) in enumerate(green_powers):
##        plt.plot(
##            red_powers,depletion_signal[:,pow_num],
##            '.-',label=('Green power = '+str(gr_pow)+' mW'))
##    plt.title('Average fluorescence signal in main lobe')
##    plt.xlabel('Red power (mW)')
##    plt.ylabel('Change in fluorescent light signal (CMOS pixel counts)')
##    plt.legend(loc='lower left')
##    plt.grid()
##    plt.figure()
##    for (pow_num,rd_pow) in enumerate(red_powers):
##        plt.plot(
##            green_powers,depletion_signal[pow_num,:],
##            '.-',label=('Red power = '+str(rd_pow)+' mW'))
##    plt.title('Average fluorescence signal in main lobe')
##    plt.xlabel('Green power (mW)')
##    plt.ylabel('Change in fluorescent light signal (CMOS pixel counts)')
##    plt.legend(loc='upper right')
##    plt.grid()
##    plt.show()
    

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
