import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter

from parse import get_var
from process import detrend_signal, taper_signal, calc_spectrum, roll_mean
from setup import all_puos, variables, metadata, window_functions, unique_dates, \
    labels, WINDOWS_MIN, SAMPLE_RATE, KERNEL_SIZE, MITTELUNGSINTERVALL


grid_kwargs =           {"color":"lightgrey", "lw":0.4}
line_kwargs =           {"color":"mediumblue", "lw":0.6}
smooth_spec_kw_args =   {"lw": 1.0, "alpha": 0.5, "c": "r"}
title_kwargs =          {"fontweight":"bold", "fontsize":12, "color":"grey", "y":1.05}
scat_kw_args =          {"s": 1.0, "alpha": 0.6, "c": "darkgrey"}
range_kw_args =         {"alpha": 0.1, "color": "orange"}

rename_dict = {
            "EXPE_t": "Temperatur \n(EXPE)",
            "SONIC_t": "Temperatur \n(SONIC)",
            "SONIC_wind_h": "Horizontalwind \n(SONIC)",
            "SONIC_wind_z": "Vertikalwind \n(SONIC)"
            }    

first_n = 300 # reduce spectra to first 300 rows

def plot_ts(
        x: np.ndarray, y: np.ndarray,
        fn: str, title: str
        ) -> None:
    """Plots the processing steps (raw, detrend, taper) of a time series."""
    
    fig, ax = plt.subplots(nrows=3, ncols=1, sharex=True, figsize=(9,6), 
                           gridspec_kw={'hspace': 0.4})
    
    # plot data
    ax[0].set_title("A. Originale Zeitreihe", loc="left")
    ax[0].plot(x, y, **line_kwargs)
    ax[1].set_title("B. Zeitreihe nach Trendbereinigung", loc="left")
    ax[1].plot(x, detrend_signal(y), **line_kwargs)
    ax[2].set_title("C. Zeitreihe nach Tapering", loc="left")
    ax[2].plot(x, taper_signal(detrend_signal(y), 0.1), **line_kwargs)
    
    # plot config
    fig.suptitle(title, **title_kwargs)
    ax[2].set_xlabel("Zeit [UTC]")
    for row_i in range(3):
        ax[row_i].xaxis.set_major_formatter(DateFormatter('%H:%M'))
        ax[row_i].set_xlim(x[0], x[-1])
        ax[row_i].grid(True, **grid_kwargs)
    
    plt.savefig(f"plots/preprocessing/preprocess_{fn}.png", dpi=600, bbox_inches="tight")
    plt.close()
    
def plot_spectrum(
        x: np.ndarray, y: np.ndarray,
        fn: str, ylabel: str, title: str
        ) -> None:
    """Plots the spectrum of a time series."""

    y_tapered = taper_signal(detrend_signal(y), 0.1)
    freq, spec = calc_spectrum(x, y_tapered)
    
    fig, ax = plt.subplots(nrows=2, ncols=1, figsize=(9,6), 
                           gridspec_kw={'hspace': 0.4})
    fig.suptitle(title, **title_kwargs)
    
    ax[0].plot(x, y_tapered, label="Zeitreihe nach Tapering", **line_kwargs)
    ax[1].scatter(freq, spec, label="Spektrum", **scat_kw_args)
    ax[1].plot(freq, roll_mean(spec, win_len=10), label=f"Gleitendes Mittel (Fensterbreite={KERNEL_SIZE})", **smooth_spec_kw_args)
    ax[1].axvspan(1/(60*30), 1/(60*60), label="30 min - 60 min", **range_kw_args)
    
    ax[0].xaxis.set_major_formatter(DateFormatter('%H:%M'))
    ax[0].set_xlim(x[0], x[-1])
    ax[0].set_xlabel("Zeit [UTC]")
    ax[0].set_ylabel(ylabel)
    ax[1].set_xlabel("Frequenz [Hz]")
    ax[1].set_ylabel("Spektrale Energiedichte * Frequenz")
    ax[1].set_xscale("log")
    ax[1].set_xlim((1e-4, 1e-1))
    ax[1].set_xticks([1e-4, 1e-3, 1e-2, 1e-1])
    ax2 = ax[1].secondary_xaxis(-0.3, functions=(lambda x: 1/x, lambda x: 1/x))
    ax2.set_xticks([10000, 1000, 100, 10])
    ax2.set_xlabel("Periodendauer [s]")
    
    for i in [0,1]:
        ax[i].grid(True)
        ax[i].legend(loc="upper left", fontsize=12)
        
    plt.savefig(f"plots/spectra/spec_{fn}.png", dpi=600, bbox_inches="tight")
    plt.close()
    
def plot_spectrum_comp(device: str) -> None:
    """Plots a comparison of all smoothed spectra."""
    
    labels = {
        "t_spec": "Temperatur [°C]",
        "wind_h_spec": "Horizontalwind [m/s]",
        "wind_z_spec": "Vertikalwind [m/s]"
        }
    
    for var in variables[device]:
        var = var+"_spec"
        fig, ax = plt.subplots(3, 4, figsize=(19, 11), sharex=False, sharey=False)
        fig.suptitle(labels[var]+f"\n\n({device}, {SAMPLE_RATE[device]} Hz)", **title_kwargs)
    
        for i, puo in enumerate(all_puos):
            df = pd.read_csv(f"data/spectra_data/{puo}_{device}_spectrum_data.csv")
            
            # plot data            
            lns1 = ax[i // 4, i % 4].scatter(df["frequencies"], df[var], s=0.5, alpha=0.5, 
                                     color="grey", label="Spektrum")
            lns2 = ax[i // 4, i % 4].plot(df["frequencies"], roll_mean(df[var], win_len=10), 
                                  lw=0.5, c="r", label=f"Gleitendes Mittel (Fensterbreite={KERNEL_SIZE})")
            lns3 = ax[i // 4, i % 4].axvspan(1/(60*30), 1/(60*60), label="30 min - 60 min", 
                                     **range_kw_args)
            
            # plot setup
            _, _, start_datetime, end_datetime, date, _ = metadata(puo)
            ax[i // 4, i % 4].set_title(f"{date}: {start_datetime[10:-3]} - {end_datetime[10:-3]}", **title_kwargs)
            
            ax[i // 4, i % 4].set_xlim((1e-4, 1e-1))
            ax[i // 4, i % 4].set_xticks([1e-4, 1e-3, 1e-2, 1e-1])
            ax[i // 4, i % 4].set_xscale("log")
            ax[i // 4, i % 4].set_xlabel("Frequenz [Hz]")
            ax[i // 4, i % 4].grid()
            ax[2, 3].axis('off')
            ax2 = ax[i // 4, i % 4].secondary_xaxis(-0.35, functions=(lambda x: 1/x, lambda x: 1/x))
            ax2.set_xticks([10000, 1000, 100, 10])
            ax2.set_xlabel("Periodendauer [s]")
            
        fig.text(-0.02, 0.5, "Spektrale Energiedichte * Frequenz", va='center', rotation='vertical', fontsize=12)
        plt.tight_layout()
        plt.savefig(f"plots/spectra_comparison/spectra_temporal_comparison_{device}_{var}.png", dpi=600, bbox_inches="tight")
        plt.close()

def plot_spectrum_comp_all() -> None:
    """Plots a comparison of all smoothed spectra for both devices."""
    
    fig, ax = plt.subplots(3, 4, figsize=(19, 11), sharex=False, sharey=False)

    for i, puo in enumerate(all_puos):
        
        ax[i // 4, i % 4].axvspan(1/(60*30), 1/(60*60), label="30 min - 60 min", 
                                    **range_kw_args)
        
        # EXPE temp
        df = pd.read_csv(f"data/spectra_data/{puo}_EXPE_spectrum_data.csv")
        ln1 = ax[i // 4, i % 4].plot(df["frequencies"], roll_mean(df["t_spec"], win_len=10), 
                        lw=0.5, c="darkorange", ls="-", label="Temperatur in °C (EXPE, 1 Hz)")
        # SONIC temp
        df = pd.read_csv(f"data/spectra_data/{puo}_SONIC_spectrum_data.csv")
        ln2 = ax[i // 4, i % 4].plot(df["frequencies"], roll_mean(df["t_spec"], win_len=10), 
                        lw=0.5, c="r", ls="-", label="Temperatur in °C (SONIC, 2 Hz)")
            
        # horizontal wind
        df = pd.read_csv(f"data/spectra_data/{puo}_SONIC_spectrum_data.csv")
        ln1 = ax[i // 4, i % 4].plot(df["frequencies"], roll_mean(df["wind_h_spec"], win_len=10), 
                        lw=0.5, c="b", label="Horizontalwind in m/s (2 Hz)")
        
        # vertical wind
        df = pd.read_csv(f"data/spectra_data/{puo}_SONIC_spectrum_data.csv")
        ln2 = ax[i // 4, i % 4].plot(df["frequencies"], roll_mean(df["wind_z_spec"], win_len=10), 
                        lw=0.5, c="g", label="Vertikalwind in m/s (2 Hz)")
        
        _, _, start_datetime, end_datetime, date, _ = metadata(puo)
        ax[i // 4, i % 4].set_title(f"{date}: {start_datetime[10:-3]} - {end_datetime[10:-3]}", **title_kwargs)
        
        ax[i // 4, i % 4].set_xlim((1e-4, 1e-1))
        ax[i // 4, i % 4].set_xticks([1e-4, 1e-3, 1e-2, 1e-1])
        ax[i // 4, i % 4].set_xscale("log")
        ax[i // 4, i % 4].set_xlabel("Frequenz [Hz]")
        ax[i // 4, i % 4].grid()
        
        ax2 = ax[i // 4, i % 4].secondary_xaxis(-0.35, functions=(lambda x: 1/x, lambda x: 1/x))
        ax2.set_xticks([10000, 1000, 100, 10])
        ax2.set_xlabel("Periodendauer [s]")
    
    
    fig.text(-0.02, 0.5, "Spektrale Energiedichte * Frequenz", va='center', rotation='vertical', fontsize=12)
    
    # ax[2, 3].set_visible(False)        
    ax[2, 3].axis('off')
        
    # ax[0, 0].legend(loc='upper right')
    lns = ln1+ln2
    labs = [l.get_label() for l in lns]
    leg = ax[2, 3].legend(lns, labs, loc="center", fontsize="14")
    for line in leg.get_lines():
        line.set_linewidth(4.0)
            
    plt.tight_layout()
    plt.savefig(f"plots/spectra_comparison/spectra_temporal_comparison.png", dpi=600, bbox_inches="tight")
    plt.close()

def plot_wind_spectrum_comp() -> None:
    """Plots a comparison of all smoothed spectra for both devices."""
    
    fig, ax = plt.subplots(3, 4, figsize=(19, 11), sharex=False, sharey=False)

    for i, puo in enumerate(all_puos):
        
        ax[i // 4, i % 4].axvspan(1/(60*30), 1/(60*60), label="30 min - 60 min", 
                                    **range_kw_args)
        
        # horizontal wind
        df = pd.read_csv(f"data/spectra_data/{puo}_SONIC_spectrum_data.csv")
        ln1 = ax[i // 4, i % 4].plot(df["frequencies"], roll_mean(df["wind_h_spec"], win_len=10), 
                        lw=0.5, c="b", label="Horizontalwind in m/s (2 Hz)")
        
        # vertical wind
        df = pd.read_csv(f"data/spectra_data/{puo}_SONIC_spectrum_data.csv")
        ln2 = ax[i // 4, i % 4].plot(df["frequencies"], roll_mean(df["wind_z_spec"], win_len=10), 
                        lw=0.5, c="g", label="Vertikalwind in m/s (2 Hz)")
            
        _, _, start_datetime, end_datetime, date, _ = metadata(puo)
        ax[i // 4, i % 4].set_title(f"{date}: {start_datetime[10:-3]} - {end_datetime[10:-3]}", **title_kwargs)
        
        ax[i // 4, i % 4].set_xlim((1e-4, 1e-1))
        ax[i // 4, i % 4].set_xticks([1e-4, 1e-3, 1e-2, 1e-1])
        ax[i // 4, i % 4].set_xscale("log")
        ax[i // 4, i % 4].set_xlabel("Frequenz [Hz]")
        ax[i // 4, i % 4].grid()
        
        ax2 = ax[i // 4, i % 4].secondary_xaxis(-0.35, functions=(lambda x: 1/x, lambda x: 1/x))
        ax2.set_xticks([10000, 1000, 100, 10])
        ax2.set_xlabel("Periodendauer [s]")
    
    
    fig.text(-0.02, 0.5, "Spektrale Energiedichte * Frequenz", va='center', rotation='vertical', fontsize=12)
    ax[2, 3].axis('off')
    lns = ln1+ln2
    labs = [l.get_label() for l in lns]
    leg = ax[2, 3].legend(lns, labs, loc="center", fontsize="14")
    for line in leg.get_lines():
        line.set_linewidth(4.0)
            
    plt.tight_layout()
    plt.savefig(f"plots/spectra_comparison/spectra_temporal_comparison_SONIC_wind.png", dpi=600, bbox_inches="tight")
    plt.close()



def plot_avg(x: np.ndarray, y: np.ndarray, device: str, title: str, fn: str) -> dict:
    """Plots the average of a time series."""

    fig, ax = plt.subplots(nrows=3, ncols=1, figsize=(10,7))
    fig.suptitle(title, **title_kwargs)
    
    colors = ["b", "cyan", "gold", "orange", "r"]
    lw = {"EXPE": 0.8, "SONIC": 0.4}
    
    # plot detrended signal
    ax[0].set_title("A. Trendbereinigtes Signal", loc="left")
    y_det = detrend_signal(y)
    ax[0].plot(x, y_det, color="grey", lw=lw[device])
    ax[0].xaxis.set_major_formatter(DateFormatter('%H:%M'))
    
    
    win_lens = [i*60*SAMPLE_RATE[device] for i in WINDOWS_MIN]
    ref = roll_mean(y_det, win_len=MITTELUNGSINTERVALL*60*SAMPLE_RATE[device])
    
    diff_lists = []
    error_metrics = {"Mean": [], "Std": [], "Lower Range": [], "Upper Range": []}
    
    for i, win_len in enumerate(win_lens):
        
        # plot rolling mean
        ax[1].set_title("B. Gleitendes Mittel verschiedener Fensterbreiten", loc="left")    
        y_roll = roll_mean(y_det, win_len)
        ax[1].plot(x, y_roll, color=colors[i], lw=lw[device], 
                   label=f"{WINDOWS_MIN[i]} min")
        ax[1].xaxis.set_major_formatter(DateFormatter('%H:%M'))
        
        # calculate error metrics
        diff = [i-j for i, j in zip(y_roll, ref)]
        diff_lists.append(diff)
        error_metrics["Std"].append(np.round(np.sum([x**2 for x in diff])/(len(ref)-1), 2))
        error_metrics["Lower Range"].append(np.round(np.min(diff), 2))
        error_metrics["Upper Range"].append(np.round(np.max(diff), 2))
        error_metrics["Mean"].append(np.round(np.mean(diff), 2))

    # plot deviation from reference    
    # sns.violinplot(data=diff_lists, ax=ax[2], palette=colors, 
    #                alpha=0.5, saturation=0.8,
    #                inner_kws=dict(box_width=5, whis_width=2, color="grey"),
    #                )
    
    # create a boxplot instead of violinplot with each box have a single color from colors
    for i, diff_list in enumerate(diff_lists):
        ax[2].boxplot(diff_list, positions=[i], widths=0.25, notch=True, showfliers=False,
                      patch_artist=True, 
                      boxprops=dict(facecolor=colors[i], color="k", alpha=0.6),
                      medianprops=dict(color="k"),
                      whiskerprops=dict(color="k"),
                      capprops=dict(color="k"),
                    #   flierprops=dict(color=colors[i], markeredgecolor="k"),
                      )
    
        
    ax[2].set_title(f"C. Abweichung vom Referenzwert ({MITTELUNGSINTERVALL} min - Mittel)", loc="left")
    ax[2].set_xticks(np.arange(5))
    ax[2].set_xticklabels([f"""{WINDOWS_MIN[i]} min \n Std = {error_metrics['Std'][i]} \n Range = ({error_metrics['Lower Range'][i]}, {error_metrics['Upper Range'][i]})""" for i in range(len(WINDOWS_MIN))])
    
    
    for row_i in [0, 1, 2]:
        ax[row_i].grid(True)
    
    plt.tight_layout()
    plt.savefig(f"plots/averaging/{fn}_{MITTELUNGSINTERVALL}min.png", dpi=600, bbox_inches="tight")
    plt.close()
    return error_metrics

def plot_win() -> None:
    """Plots the nonparametric window functions."""
    
    _, ax = plt.subplots(nrows=4, ncols=4, figsize=(10, 10),
                           sharex=True, sharey=True)
    
    for i, wf in enumerate(window_functions):
        
        # plot full range
        ax[i//4, i%4].plot(
            np.arange(100), 
            taper_signal(y=np.ones(100), perc=0.5, func=wf),
            c="grey", lw=0.8, label="Gesamte Breite")
        
        # taper only first and last 10 %
        ax[i//4, i%4].plot(
            np.arange(100), 
            taper_signal(y=np.ones(100), perc=0.1, func=wf),
            c="navy", lw=0.8, label="Äußeren 10 %")
        
        ax[i//4, i%4].set_title(wf.__name__)
        ax[i//4, i%4].grid(which="both", axis="both", alpha=0.2)

    ax[0, 0].legend(loc='center')
    plt.savefig("plots/sensitivity_wf/window_functions.png", dpi=600, bbox_inches="tight")
    plt.close()

def plot_win_influence(x: np.ndarray, y: np.ndarray, title: str, fn: str) -> None:
    """Plots the influence of different window functions on the spectrum."""
    
    fig, ax = plt.subplots(nrows=4, ncols=4, figsize=(10, 10),
                           sharex=True, sharey=True)
    
    fig.suptitle(title, **title_kwargs)
    
    for i, wf in enumerate(window_functions):
        freq, spec = calc_spectrum(x, taper_signal(detrend_signal(y), 0.1, func=wf))
        spec_roll = roll_mean(spec, win_len=10)
        
        ax[i//4, i%4].plot(freq, spec_roll, 
                           label=wf.__name__, c="navy", lw=0.4)
        ax[i//4, i%4].set_xscale("log")
        ax[i//4, i%4].set_xlim((1e-4, 1e-1))
        ax[i//4, i%4].set_xticks([1e-4, 1e-3, 1e-2, 1e-1])
        ax[i//4, i%4].set_title(wf.__name__)
        ax[i//4, i%4].grid(which="both", axis="both", alpha=0.2)

    plt.savefig(f"plots/sensitivity_wf/{fn}.png", dpi=600, bbox_inches="tight")
    plt.close()

def plot_temporal_coverage() -> None:
    """Plots the temporal coverage of the experiments."""
    
    _, ax = plt.subplots(nrows=2, ncols=3, figsize=(14,7), 
                         sharex=False, sharey=True, 
                         gridspec_kw = {'wspace':0, 'hspace':1})
    
    for i in range(len(unique_dates)):
        row_i = i // 3
        col_i = i % 3
        
        # get data
        period = f"Day{i+1}"
        expe_dt = get_var("EXPE", period, "Datetime")
        expe_t = get_var("EXPE", period, "t")
        sonic_dt = get_var("SONIC", period, "Datetime")
        sonic_t = get_var("SONIC", period, "t")
        sonic_h = get_var("SONIC", period, "wind_h")
                
        ax2 = ax[row_i, col_i].twinx()
        
        # plot data
        lns1 = ax[row_i, col_i].plot(
            sonic_dt, sonic_t, label="SONIC Temperatur", 
            lw=0.3, ls = "solid", alpha=0.6, c="darkblue")
        lns2 = ax[row_i, col_i].plot(
            expe_dt, expe_t, label="EXPE Temperatur", 
            lw=0.5, ls="solid", alpha=0.6, c="blue")
        lns3 = ax2.plot(
            sonic_dt, sonic_h, label="SONIC Horizontalwind",
            lw=0.3, alpha=0.6, c="r", )
    
        # highlight puos
        ranges = []
        for puo in all_puos:
            _, _, start_date, end_date, _, day = metadata(puo)
            start = pd.to_datetime(start_date, format="%Y-%m-%d %H:%M:%S")
            end = pd.to_datetime(end_date, format="%Y-%m-%d %H:%M:%S")
            ranges.append((day-1, start, end))
            
        for j in range(len(ranges)): 
            ax_i, start, end = ranges[j]
            if ax_i == i:
                hours = round((end-start).total_seconds()/(60*60), 1)
                ax[row_i, col_i].axvspan(ranges[j][1], ranges[j][2], alpha=0.1, 
                                         color='gold', label=f"PUO {j+1}: {hours} h")
        
        # plot config
        ax[row_i, col_i].set_title(f"Messtag {i+1}: {unique_dates[i]}", loc="left", **title_kwargs)
        ax[row_i, 0].set_ylabel("Temperatur [°C]", color="darkblue")
        ax[row_i, col_i].set_xlabel("Zeit [UTC]")
        ax[row_i, col_i].set_ylim((10,45))
        ax[row_i, col_i].xaxis.set_major_formatter(DateFormatter('%H:%M'))
        ax[row_i, col_i].grid(True)
        
        ax2.set_ylim((0, 10))
        if col_i == 2:
            ax2.set_ylabel("Windgeschw. [m/s]", color="r")
        else:
            pass
        if col_i != 2:
            ax2.set_yticks([])
        
        date = unique_dates[i]
        da, mo, ye = date.split(".")
        ax[row_i, col_i].set_xlim((
                pd.Timestamp(int(ye), int(mo), int(da), 5, 0), 
                pd.Timestamp(int(ye), int(mo), int(da), 17, 0)
                ))
        
        lns = lns1+lns2+lns3
        labs = [l.get_label() for l in lns]
        leg = ax[1, 2].legend(lns, labs, loc="center", fontsize="14")
        for line in leg.get_lines():
            line.set_linewidth(4.0)
            
        ax[1, 2].axis('off')
        
    plt.tight_layout()
    plt.savefig("plots/temporal_coverage/temporal_coverage.png", 
                dpi=600, bbox_inches='tight')
    plt.close()


def plot_patterns(period: str) -> None:
    """Plot all spectra for a single period under observation."""
    
    _, ax = plt.subplots(1, 1, figsize=(8, 5))
    
    # read spectra data
    df = pd.read_csv(f"data/spectra_data/{period}_comparison_spectrum_data.csv")
    
    # norm spectra
    df = (df-df.min())/(df.max()-df.min())
    
    # calculate mean and std
    df["mean"] = df.mean(axis=1)
    df["std"] = df.std(axis=1)
    
    # reduce spectra to first n rows
    df = df.iloc[1:, :]
    df = df.iloc[:first_n, :]
    
    # plot spectra
    x = df["frequencies"]
    plt.plot(x, roll_mean(df["EXPE_t"], win_len=10), label="Temperatur (EXPE)", 
             lw=1.0, ls="--", c="red", alpha=0.6)
    plt.plot(x, roll_mean(df["SONIC_t"], win_len=10), label="Temperatur (SONIC)", 
             lw=1.0, ls="solid", c="r", alpha=0.6)
    plt.plot(x, roll_mean(df["SONIC_wind_h"], win_len=10), label="Horizontalwind (SONIC)", 
             lw=1.0, ls="solid", c="b", alpha=0.6)
    plt.plot(x, roll_mean(df["SONIC_wind_z"], win_len=10), label="Vertikalwind (SONIC)", 
             lw=1.0, ls="solid", c="darkgreen", alpha=0.6)
    
    # plot mean and confidence interval
    # plt.plot(x, roll_mean(df["mean"], win_len=10), label="Mittelwert",
    #             lw=1.0, ls="solid", c="k")
    # plt.fill_between(x, roll_mean(df["mean"]-0.5*df["std"], win_len=10),
    #                     roll_mean(df["mean"]+0.5*df["std"], win_len=10),
    #                     color="grey", alpha=0.3, label="Konfidenzinvervall")
    
    # plot 30 to 60 min range
    plt.axvspan(1/(60*30), 1/(60*60), label="30 min - 60 min", **range_kw_args)
    
    # plot setup
    _, _, start_datetime, end_datetime, date, _ = metadata(period)
    plt.title(f"{date}: {start_datetime[10:-3]} - {end_datetime[10:-3]}", **title_kwargs)
    plt.ylim(bottom=-0.1)
    plt.ylabel("Spektrale Energiedichte * Frequenz (min-max-normiert)")
    plt.xlabel("Frequenz [Hz]")
    plt.xscale("log")
    plt.xlim((1e-4, 1e-1))
    plt.xticks([1e-4, 1e-3, 1e-2, 1e-1])
    plt.legend(loc="upper left")
    plt.grid()
    ax2 = ax.secondary_xaxis(-0.15, functions=(lambda x: 1/x, lambda x: 1/x))
    ax2.set_xticks([10000, 1000, 100, 10])
    ax2.set_xlabel("Periodendauer [s]")
    plt.savefig(f"plots/spectra_comparison/spectra_variable_comparison_{period}.png", bbox_inches="tight", dpi=600)
    plt.close()
    
    
    # correlation matrix
    _, ax = plt.subplots(1, 1, figsize=(7.5, 6))
    
    # read spectra data
    df = pd.read_csv(f"data/spectra_data/{period}_comparison_spectrum_data.csv")
    
    # norm spectra
    df = (df-df.min())/(df.max()-df.min())
    
    # reduce spectra to first n rows
    df = df.iloc[:first_n, :]
    df = df.iloc[:, 1:]
    
    # calculate rolling mean
    df = df.apply(roll_mean, win_len=10)
    
    # rename columns
    df = df.rename(columns=rename_dict)

    # calculate correlation matrix    
    df_corr = df.corr(method="pearson")
    
    # plot data
    _, _, start_datetime, end_datetime, date, _ = metadata(period)
    plt.title(f"Pearson-Korrelation der Energiespektren\n{date}: {start_datetime[10:-3]} - {end_datetime[10:-3]}", **title_kwargs)
    sns.heatmap(df_corr, 
                mask=np.eye(len(df_corr)), 
                center=0, 
                annot=True, fmt=".2f",
                linewidths=.5,
                cmap="vlag", vmin=-1, vmax=1,
                )
    plt.savefig(f"plots/spectra_comparison/spectra_variable_comparison_corr_{period}.png", bbox_inches="tight", dpi=600)
    plt.close()

    
def plot_mean_corr():
    """Plots the mean correlation matrix of all periods under observation."""
    
    # calculate mean correlation
    corr_dfs = []
    for period in all_puos:
        df = pd.read_csv(f"data/spectra_data/{period}_comparison_spectrum_data.csv")
        
        # reduce spectra to first 300 rows
        
        df = df.iloc[:first_n, :]
        df = df.apply(roll_mean, win_len=10)
        

        df = df.rename(columns=rename_dict)
        df = df.iloc[:, 1:]
        df = (df-df.min())/(df.max()-df.min())
        corr_dfs.append(df.corr(method="pearson"))
        
    # calculate mean correlation 
    df_corr = pd.concat(corr_dfs).groupby(level=0).mean()
    df_corr = df_corr.reindex(index=df_corr.columns)
    
    # Plot correlation matrix
    plt.figure(figsize=(7.5, 6))
    plt.title("Mittlere Korrelation der Energiespektren", **title_kwargs)
    sns.heatmap(df_corr, 
                mask=np.eye(len(df_corr)), 
                center=0, 
                annot=True, fmt=".2f",
                linewidths=.5,
                cmap="vlag", vmin=-1, vmax=1
                )
    
    plt.savefig(f"plots/other/correlation_mean.png", bbox_inches="tight", dpi=600)
    plt.close()

def plot_turb_intensity(which: str) -> None:

    plt.figure(figsize=(7, 4))
    
    colors = {
        "EXPE_t": "r",
        "SONIC_t": "darkred",
        "SONIC_wind_h": "b", 
        "SONIC_wind_z": "g"
        }
    
    for period in all_puos:
        _, _, start_datetime, end_datetime, date, _ = metadata(period)
        if period != "PUO_05":
            for device in ["EXPE", "SONIC"]:
                df = pd.read_csv(f"data/turbulence_intensity_data/{period}_{device}_turbulence_intensity_data.csv")
                df["time"] = df["from"].apply(lambda x: x[11:16])
                
                for var in variables[device]:
                    x = [f"{str(i).zfill(2)}:{str(j).zfill(2)}" for i in range(24) for j in range(0, 60, 10)]
                    y = [np.nan for _ in range(len(x))]

                    for i in range(len(df)):
                        if which == "abs":
                            y[x.index(df["time"][i])] = df[f"{var}_abs"][i]
                        elif which == "rel":
                            y[x.index(df["time"][i])] = df[f"{var}_rel"][i]
                    
                        plt.scatter(x, y, label=f"{device}: {labels[var]}", 
                                lw=0.5, color=colors[f"{device}_{var}"], 
                                alpha=0.5, s=10, zorder=10
                                )
    
    plt.ylabel("Turbulenzintensität")
    plt.xlabel("Zeit [UTC]")
    plt.grid()
    plt.xticks([f"{str(i).zfill(2)}:00" for i in range(6,18,1)], rotation=90)
    if which == "abs":
        pass
    else:
        plt.ylim([0,3.5])
    
    leg_handles, leg_labels = plt.gca().get_legend_handles_labels()
    by_label = dict(zip(leg_labels, leg_handles))
    plt.legend(by_label.values(), by_label.keys(), loc="lower center", ncol=2,
               bbox_to_anchor=(0.5, 1.0), fontsize=8)
    
    plt.savefig(f"plots/turbulent_intensity/turbulent_intensity_{which}_without_PUO05.png", dpi=600, bbox_inches="tight")
    plt.close()
    
def plot_error_metrics(fn: str = "data/avg_error_metrics.csv") -> None:
    from setup import labels, all_puos

    # Read data
    df = pd.read_csv(fn)
    df = df[df["Variable"] != "wind_z"]
    df = df[df["Variable"] != "wind_h"]

    # remove first puo from all_puos because it is an outlier
    all_puos = all_puos[1:]

    # Plot
    _, ax = plt.subplots(nrows=2, ncols=3, figsize=(11, 8), sharey=True)

    def get_data(df, device: str, puo: str, metric: str) -> list[float]:
        """Helper function to provide data for plotting."""
        df_sub = df.copy()
        df_sub = df[df["Device"] == device]
        df_sub = df_sub[df_sub["PUO"] == puo]
        arr = df_sub[metric].to_numpy()[0]
        arr = arr[1:-1].split(", ")
        arr = [float(val) for val in arr]
        return arr

    offsets = np.linspace(-0.25, 0.25, 10)
    colors = ["b", "cyan", "gold", "orange", "r"]

    plotting_agenda = {
        (0,0): "Std",
        (1,0): "Std",
        (0,1): "Lower Range",
        (1,1): "Lower Range",
        (0,2): "Upper Range",
        (1,2): "Upper Range"
        }
    
    for i, puo in enumerate(all_puos):
        off = offsets[i]

        for (row_i, col_i) in [(0,0), (1,0), (0,1), (1,1), (0,2), (1,2)]:

            # EXPE
            barlist = ax[0, col_i].barh(
                y=[j + off for j in range(5)], 
                width=get_data(df, device="EXPE", puo=puo, metric=plotting_agenda[row_i, col_i]), 
                height=0.02, label=puo, zorder=2, alpha=0.8)
            for i in range(5):
                barlist[i].set_color(colors[i])
        
            # SONIC
            barlist = ax[1, col_i].barh(
                y=[j + off for j in range(5)], 
                width=get_data(df, device="SONIC", puo=puo, metric=plotting_agenda[row_i, col_i]), 
                height=0.02, label=puo, zorder=2, alpha=0.8)
            for i in range(5):
                barlist[i].set_color(colors[i])
                
    for (row_i, col_i) in [(0,0), (1,0), (0,1), (1,1), (0,2), (1,2)]:
        ax[row_i, col_i].set_yticks(range(5))
        ax[row_i, col_i].set_yticklabels([1, 5, 10, 30, 60])    
        ax[row_i, col_i].grid(color="grey", alpha=0.4)
        ax[row_i, 0].set_xlim([0, 2])
        ax[row_i, 1].set_xlim([-4.5, 0])
        ax[row_i, 2].set_xlim([0, 4.5])

    ax[0,1].text(-2.5, 5.25, "EXPE", color="grey", fontsize=13, fontweight="bold")
    ax[1,1].text(-2.5, 5.25, "SONIC", color="grey", fontsize=13, fontweight="bold")
    for row_i in range(2):
        ax[row_i, 0].set_ylabel("Mittelungsfenster [min]", color="grey", fontsize=11, fontweight="bold")
        ax[row_i,0].set_title("A. Standardabweichung [°C]", loc="left", color="grey", fontsize=10, fontweight="bold")
        ax[row_i,1].set_title("B. Maximale Unterschätzung [°C]", loc="left", color="grey", fontsize=10, fontweight="bold")
        ax[row_i,2].set_title("C. Maximale Überschätzung [°C]", loc="left", color="grey", fontsize=10, fontweight="bold")

        
    plt.subplots_adjust(wspace=0.05, hspace=0.4)
    plt.savefig(f"plots/other/error_metrics_{MITTELUNGSINTERVALL}min.png", dpi=600, bbox_inches="tight")
    plt.close()