import matplotlib.patches as mpatches
import pandas as pd
import datetime
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from shutil import copyfile
from collections import defaultdict
from matplotlib.patches import Rectangle
from colors_and_countries import *
from travel_data import *

figure_path = "../cluster_scripts/figures/"

grey_color = "#cccccc"
fmt = "pdf"

clusters = {"S477": {'snps': [22991, 4542], 'cluster_data': [],
            'country_info':[], 'col': "#ff8d3d"},
            "S222": {'snps': [22226, 28931, 29644], 'cluster_data': [],
            "country_info":[], 'col': "#65beeb"}
            }

# Get diagnostics file - used to get list of SNPs of all sequences, to pick out seqs that have right SNPS
diag_file = "results/sequence-diagnostics.tsv"
diag = pd.read_csv(diag_file, sep='\t', index_col=False)
# Read metadata file
input_meta = "data/metadata.tsv"
meta = pd.read_csv(input_meta, sep='\t', index_col=False)

for clus in clusters.keys():

    print(f"Running cluster {clus}")
    snps = clusters[clus]['snps']

    # get the sequences that we want - which are 'part of the cluster:
    wanted_seqs = []

    for index, row in diag.iterrows():
        strain = row['strain']
        snplist = row['all_snps']
        if not pd.isna(snplist):
            intsnp = [int(x) for x in snplist.split(',')]
            if all(x in intsnp for x in snps):
                #if meta.loc[meta['strain'] == strain].region.values[0] == "Europe":
                wanted_seqs.append(row['strain'])

    # There's one spanish seq with date of 7 March - we think this is wrong.
    # If seq there and date bad - exclude!
    bad_seq = meta[meta['strain'].isin(['Spain/VC-IBV-98006466/2020'])]
    if bad_seq.date.values[0] == "2020-03-07" and 'Spain/VC-IBV-98006466/2020' in wanted_seqs:
        wanted_seqs.remove('Spain/VC-IBV-98006466/2020')

    print(len(wanted_seqs)) # how many are there?

    cluster_meta = meta[meta['strain'].isin(wanted_seqs)]
    observed_countries = [x for x in cluster_meta['country'].unique()]

    # What countries do sequences in the cluster come from?
    print(f"The cluster is found in: {observed_countries}")


    # Let's get some summary stats on number of sequences, first, and last, for each country.
    country_info = pd.DataFrame(index=all_countries, columns=['first_seq', 'num_seqs', 'last_seq', "sept_aug_freq"])
    country_dates = {}
    cutoffDate = datetime.datetime.strptime("2020-08-01", '%Y-%m-%d')

    for coun in all_countries:
        if coun in uk_countries:
            temp_meta = cluster_meta[cluster_meta['division'].isin([coun])]
        else:
            temp_meta = cluster_meta[cluster_meta['country'].isin([coun])]
        country_info.loc[coun].first_seq = temp_meta['date'].min()
        country_info.loc[coun].last_seq = temp_meta['date'].max()
        country_info.loc[coun].num_seqs = len(temp_meta)

        country_dates[coun] = [datetime.datetime.strptime(dat, '%Y-%m-%d') for dat in temp_meta['date']]

        herbst_dates = [x for x in country_dates[coun] if x >= cutoffDate]
        if coun in uk_countries:
            temp_meta = meta[meta['division'].isin([coun])]
        else:
            temp_meta = meta[meta['country'].isin([coun])]
        all_dates = [datetime.datetime.strptime(x, '%Y-%m-%d') for x in temp_meta["date"] if len(x) is 10 and "-XX" not in x and datetime.datetime.strptime(x, '%Y-%m-%d') >= cutoffDate]
        country_info.loc[coun].sept_aug_freq = round(len(herbst_dates)/len(all_dates),2)

    print(f"\nCluster {clus}")
    print(country_info)
    print("\n\n")
    clusters[clus]['country_info'] = copy.deepcopy(country_info)

    # Get counts per week for sequences in the cluster
    clus_week_counts = {}
    for coun in all_countries:
        counts_by_week = defaultdict(int)
        for dat in country_dates[coun]:
            #counts_by_week[dat.timetuple().tm_yday//7]+=1 # old method
            counts_by_week[dat.isocalendar()[1]]+=1  #returns ISO calendar week
        clus_week_counts[coun] = counts_by_week

    # Get counts per week for sequences regardless of whether in the cluster or not - from week 20 only.
    total_week_counts = {}
    for coun in all_countries:
        counts_by_week = defaultdict(int)
        if coun in uk_countries:
            temp_meta = meta[meta['division'].isin([coun])]
        else:
            temp_meta = meta[meta['country'].isin([coun])]
        #week 20
        for ri, row in temp_meta.iterrows():
            dat = row.date
            if len(dat) is 10 and "-XX" not in dat: # only take those that have real dates
                dt = datetime.datetime.strptime(dat, '%Y-%m-%d')
                # wk = dt.timetuple().tm_yday//7  # old method
                wk = dt.isocalendar()[1] #returns ISO calendar week
                if wk >= 20:
                    counts_by_week[wk]+=1
        total_week_counts[coun] = counts_by_week

    # Convert into dataframe
    cluster_data = pd.DataFrame(data=clus_week_counts)
    total_data = pd.DataFrame(data=total_week_counts)

    # sort
    total_data=total_data.sort_index()
    cluster_data=cluster_data.sort_index()

    clusters[clus]['cluster_data'] = copy.deepcopy(cluster_data)

print("\n\nYou can check on the country_info with: clusters['S477']['country_info'] ")

#cluster_data_S477 = copy.deepcopy(cluster_data)
#cluster_data_S222 = copy.deepcopy(cluster_data)

############## Plot

#Use the S477 data to decide what to plot.
countries_to_plot = ["France", "United Kingdom", "Netherlands",
    "Switzerland"]
#Remember to adjust the number of axes if needed below....

#fig, ax1 = plt.subplots(nrows=1,figsize=(10,7))
fig, (ax1, ax2, ax3, ax4) = plt.subplots(nrows=4, sharex=True,figsize=(10,7),
                                    gridspec_kw={'height_ratios':[1,1,1,1]})

#for coun in [x for x in countries_to_plot]:
for coun, ax in zip(countries_to_plot, [ax1, ax2, ax3, ax4]):
    i=0
    first_clus_count = []
    ptchs = []
    #for cluster_data in [cluster_data_S477, cluster_data_S222]:
    for clus in clusters.keys():
        cluster_data = clusters[clus]['cluster_data']
        week_as_date, cluster_count, total_count = non_zero_counts(cluster_data, coun)

        linesty = '-'
        lab = f"{coun} {clus}"
        if i == 1:
            linesty = ':'
            cluster_count = first_clus_count + cluster_count
        ax.plot(week_as_date, cluster_count/total_count,
                color=clusters[clus]['col'],#country_styles[coun]['c'],
                linestyle=linesty)#, label=lab)
        #ax.scatter(week_as_date, cluster_count/total_count, s=[marker_size(n) for n in total_count],
        #        color=country_styles[coun]['c'],
        #        linestyle=linesty)
        if i==0:
            ax.fill_between(week_as_date, 0, cluster_count/total_count, facecolor=clusters[clus]['col'])
            patch = mpatches.Patch(color=clusters[clus]['col'], label=lab)
            ptchs.append(patch)
        else:
            ax.fill_between(week_as_date, first_clus_count/total_count, cluster_count/total_count, facecolor=clusters[clus]['col'])
            patch = mpatches.Patch(color=clusters[clus]['col'], label=lab)
            ptchs.append(patch)
            ax.fill_between(week_as_date, cluster_count/total_count, 1, facecolor=grey_color)
            patch = mpatches.Patch(color=grey_color, label=f"{coun} other")
            ptchs.append(patch)
        if i == 0:
            first_clus_count = cluster_count
        i+=1
    ax.legend(handles=ptchs, loc=3, fontsize=fs*0.7)
    ax.tick_params(labelsize=fs*0.8)
    ax.set_ylabel('frequency')
    #ax.legend(ncol=1, fontsize=fs*0.8, loc=2)

fig.autofmt_xdate(rotation=30)
plt.show()
plt.tight_layout()

plt.savefig(figure_path+f"S222_S477_compare.{fmt}")
trends_path = figure_path+f"S222_S477_compare.{fmt}"
copypath = trends_path.replace("compare", "compare-{}".format(datetime.date.today().strftime("%Y-%m-%d")))
copyfile(trends_path, copypath)
