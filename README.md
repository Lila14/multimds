# MultiMDS

MultiMDS is a tool for locus-specific structural comparisons of two Hi-C datasets. It jointly infers and aligns 3D structures from two datasets, such as different cell types. The output is aligned 3D structure files (which can be plotted, see below). 
## Installation

Requirements:
* python 2.7
    * numpy
    * pymp
    * scikit-learn
    * scipy
    * matplotlib (optional; for reproducing figures)
    * statsmodels (optional; for reproducing figures)
    * tadlib (optional; for reproducing figures)
* Python dependencies can be installed using
``pip install -r requirements.txt``
* The following optional dependencies can be installed manually:
    * [mayavi](http://docs.enthought.com/mayavi/mayavi/) (for plotting)
    * [ImageMagick](https://www.imagemagick.org/script/index.php) (for creating gifs)
    * [bedtools](http://bedtools.readthedocs.io/en/latest/content/installation.html) (for reproducing figures)
    * [edgeR](https://bioconductor.org/packages/release/bioc/html/edgeR.html) (for reproducing figures)

## TLDR

``python multimds.py --full [Hi-C BED path 1] [Hi-C BED path 2]``

## Testing

On Linux, please run test.sh (in the scripts directory) and report any issues. (multimds is compatible with Mac, but the shell scripts only run on Linux.) 

## Usage

### Input files

MultiMDS uses intrachromosomal BED files as input. Data must be normalized prior to use (for example, using [HiC-Pro](http://nservant.github.io/HiC-Pro/)). 

Format:

>chrom	bin1\_start	bin1\_end	chrom	bin2\_start	bin2\_end	normalized\_contact\_frequency

Example - chr21 data at 10-Kbp resolution:

>chr21	16050000	16060000	chr21	16050000	16060000	12441.5189291
> 
>...

Important: BED file 1 and BED file 2 must be the same species, chromosome, and resolution!

### Running the program

To view help:

``python multimds.py -h``

To run with default parameters:

``python multimds.py [BED path 1] [BED path 2]``

For example:

``python multimds.py GM12878_combined_21_100kb.bed K562_21_100kb.bed``


### Similarity weight

The parameter -P controls how similar the output structures will be. By default it is set to 0.05, but it is recommended that this be changed. 

``python multimds.py -P 0.02 GM12878_combined_21_100kb.bed K562_21_100kb.bed``

The minimum weight that can achieve reproducibility is recommended. The script reproducibility.py (in the scripts directory) plots reproducibility at different values of this parameter. Choose the parameter at which the increase in reproducibility levels off.

For example run
``python reproducibility.py GM12878_combined_21_100kb.bed K562_21_100kb.bed``


### Output files

### Relocalization peaks

Genomic regions that significantly relocalize between the cell types are saved to a BED file, with the format [PREFIX1]_[PREFIX2]_peaks.bed

For example the output of

``python multimds.py GM12878_combined_21_100kb.bed K562_21_100kb.bed``

is GM12878_combined_21_100kb_K562_21_100kb_peaks.bed

#### Structure files
Aligned structures are saved to tsv files, which can be used for plotting (see below). The header contains the name of the chromosome, the resolution, and the starting genomic coordinate. Each line in the file contains the genomic bin number followed by the 3D coordinates (with "nan" for missing data). 

Example - chr21 at 10-Kbp resolution:

>chr21
> 
>10000
> 
>16050000
> 
>0	0.589878298045	0.200029092421	0.182515056542
> 
>1	0.592088232028	0.213915817254	0.186657230841
> 
>2	nan	nan	nan
> 
>...

0 corresponds to the bin 16050000-16060000, 1 corresponds to the bin 16060000-16070000, etc. 

### Plotting

Read a structure:

    import data_tools
    structure = data_tools.structure_from_file("GM12878_combined_21_100kb_structure.tsv")``

Create an interactive 3D plot in Mayavi. (Mayavi allows you to rotate the image and save a view.)

    import plotting
    plotting.plot_structure_interactive(structure, color=(0,0.5,0.7), radius=0.01, enrichments=my_enrichments)``

If _radius_ is not selected, the to-scale radius of heterochromatin is used. 

_enrichments_ is a vector with a numerical value for each bin in the structure (i.e. bins that do not have a nan coordinate). For example, this could represent ChIP-seq enrichments for each bin. This option overrides _color_ and will use a rainbow colormap, with blue representing low values and red representing high values. 

Multiple structures can be plotted simultaneously:

    chroms = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 21, X)
    structures = [data_tools.structure_from_file("GM12878_combined_{}_100kb_structure.tsv".format(chrom) for chrom in chroms)]
    plotting.plot_structures_interactive(structures)

plotting.py has 23 built-in colors designed to be maximally different to the human eye. By default, these colors are used when plotting multiple structures. You can also specify a list of colors:

    chroms = (1, 2)
    structures = [data_tools.structure_from_file("GM12878_combined_{}_100kb_structure.tsv".format(chrom) for chrom in chroms)]
    plotting.plot_structures_interactive(structures, colors=[(1,0,0), (0,0,1)])

_all_enrichments_ is a list of enrichments, e.g. 
     
     plotting.plot_structures_interactive(structures, all_enrichments=[enrichments1, enrichments2])

The radius can also be specified, as above. 

The option _cut_ creates a cross-section of the plot. For example, this is useful for viewing the interior of the nucleus.

    chroms = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 21, X)
    structures = [data_tools.structure_from_file("GM12878_combined_{}_100kb_structure.tsv".format(chrom) for chrom in chroms)]
    plotting.plot_structures_interactive(structures, cut=True)

A plot can be saved as a gif:

``plotting.plot_structure_gif(structure, struct, color=(1,0,0), radius=None, increment=10)``

will create struct.gif

A smaller value of _increment_ will lead to a smoother gif. Increments must be a factor of 360. 

Multiple structures can also be plotted in a single gif:

``plotting.plot_structures_gif(structures, struct, colors=default_colors, radius=None, increment=10)``

#### Parameters (optional)

#### Full MDS

By default, partitioned MDS is used. To use full MDS:

``python multimds.py --full GM12878_combined_21_100kb.bed K562_21_100kb.bed``

##### Number of partitions

Partitioning is used in the structural inference step for greater efficiency and accuracy. By default 4 partitions are used. This can be controlled with the -N parameter: 

``python multimds.py -N 2 GM12878_combined_21_100kb.bed K562_21_100kb.bed``

#### Resolution ratio

Multimds first infers a global intrachromosomal structure at low resolution, which it uses as a scaffold for high-resolution inference. By default a resolution ratio of 10 is used. So if your input file is 100-kb resolution, a 1-Mb structure will be used for approximation. The resolution ratio can be changed with the l option. 

``python multimds.py -l 20 GM12878_combined_21_10kb.bed K562_21_10kb.bed``

The value you choose depends on your tradeoff between speed and accuracy (but must be an integer). Lower resolutions (i.e. higher ratios) are faster but less accurate.

##### Number of threads

Multimds uses multithreading to achieve greater speed. By default, 3 threads are requested, because this is safe for standard 4-core desktop computers. However, the number of threads used will never exceed the number of processors or the number of partitions, regardless of what is requested. You can change the number of requested threads using -n.

For example, to run multimds with four threads:

``python multimds.py -n 4 GM12878_combined_21_10kb.bed K562_21_10kb.bed``

##### Scaling factor

The scaling factor a describes the assumed relationship between contact frequencies and physical distances: distance = contact_frequency^(-1/a). The default value is 4, based on Wang et al 2016. You can change the scaling factor using -a. 

``python multimds.py -a 3 GM12878_combined_21_10kb.bed K562_21_10kb.bed``

a can be any value >1, including non-integer.
