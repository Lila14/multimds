import numpy as np
import data_tools as dt
import sys
import compartment_analysis as ca
import os
import linear_algebra as la
import array_tools as at
from scipy import signal as sg
from hmmlearn import hmm
import argparse

def normalize(values):
	return np.array(values)/max(values)

def call_peaks(data):
	"""Calls peaks using Gaussian hidden markov model"""
	reshaped_data = data.reshape(-1,1)
	model = hmm.GaussianHMM(n_components=2).fit(reshaped_data)
	scores = model.predict(reshaped_data)

	#determine if peaks are 0 or 1
	zero_indices = np.where(scores == 0)
	one_indices = np.where(scores == 1)
	zero_data = data[zero_indices]
	one_data = data[one_indices]
	if np.mean(zero_data) > np.mean(one_data):
		scores[zero_indices] = 1
		scores[one_indices] = 0

	#find boundaries of peaks
	peaks = []
	in_peak = False
	for i, score in enumerate(scores):
		if in_peak and score == 0:	#end of peak
			in_peak = False
			peak.append(i)
			peaks.append(peak)
		elif not in_peak and score == 1:	#start of peak
			in_peak = True
			peak = [i]

	return peaks

def main():
	parser = argparse.ArgumentParser(description="Identify locus-specific changes between Hi-C datasets")
	parser.add_argument("path1", help="path to intrachromosomal Hi-C BED file 1")
	parser.add_argument("path2", help="path to intrachromosomal Hi-C BED file 2")
	parser.add_argument("activity_path1", help="path to active enrichment BED file 1")
	parser.add_argument("activity_path2", help="path to active enrichment BED file 2")
	parser.add_argument("-N", default=4, help="number of partitions")
	parser.add_argument("-m", default=0, help="genomic coordinate of centromere")
	args = parser.parse_args()

	n = 5

	prefix1 = args.path1.split(".")[0]
	prefix2 = args.path2.split(".")[0]

	min_error = sys.float_info.max
	for iteration in range(n):
		os.system("python .minimds.py -m {} -N {} -o {}_ {} {}".format(args.centromere, args.num_partitions, iteration, args.path1, args.path2))
		
		#load structures
		structure1 = dt.structure_from_file("{}_{}_structure.tsv".format(iteration, prefix1, res_kb))	
		structure2 = dt.structure_from_file("{}_{}_structure.tsv".format(iteration, prefix2, res_kb))

		#rescale
		structure1.rescale()
		structure2.rescale()

		#make structures compatible
		dt.make_compatible((structure1, structure2))

		#align
		r, t = la.getTransformation(structure1, structure2)
		structure1.transform(r,t)

		#calculate error
		coords1 = np.array(structure1.getCoords())
		coords2 = np.array(structure2.getCoords())
		error = np.mean([la.calcDistance(coord1, coord2) for coord1, coord2 in zip(coords1, coords2)])
		if error < min_error:
			min_error = error
			best_iteration = iteration

	for iteration in range(n):
		if iteration == best_iteration:
			#load structures
			structure1 = dt.structure_from_file("{}_{}_structure.tsv".format(iteration, prefix1, res_kb))	
			structure2 = dt.structure_from_file("{}_{}_structure.tsv".format(iteration, prefix2, res_kb))
		else:
			os.system("rm {}_{}_structure.tsv".format(iteration, prefix1, res_kb))	
			os.system("rm {}_{}_structure.tsv".format(iteration, prefix2, res_kb))		

	#rescale
	structure1.rescale()
	structure2.rescale()

	#make structures compatible
	dt.make_compatible((structure1, structure2))

	#align
	r, t = la.getTransformation(structure1, structure2)
	structure1.transform(r,t)

	#calculate error
	coords1 = np.array(structure1.getCoords())
	coords2 = np.array(structure2.getCoords())
	dists = [la.calcDistance(coord1, coord2) for coord1, coord2 in zip(coords1, coords2)]
	print np.mean(dists)

	#compartments
	contacts1 = dt.matFromBed(path1, structure1)
	contacts2 = dt.matFromBed(path2, structure2)
	at.makeSymmetric(contacts1)
	at.makeSymmetric(contacts2)

	compartments1 = ca.get_compartments(contacts1, structure1, args.activity_path1, chrom, res_kb), True)
	compartments2 = ca.get_compartments(contacts2, structure2, args.activity_path2, chrom, res_kb), True)	

	gen_coords = structure1.getGenCoords()

	dists = normalize(dists)
	compartment_diffs = np.abs(compartments1 - compartments2)
	compartment_diffs = normalize(compartment_diffs)

	smoothed_dists = sg.cwt(dists, sg.ricker, [smoothing_parameter])[0]
	smoothed_diffs = sg.cwt(compartment_diffs, sg.ricker, [smoothing_parameter])[0]
	dist_peaks = call_peaks(smoothed_dists)
	diff_peaks = call_peaks(smoothed_diffs)

	with open("dist_peaks.bed", "w") as out:
		for peak in dist_peaks:
			start, end = peak
			peak_dists = dists[start:end]
			max_dist_index = np.argmax(peak_dists) + start
			out.write("\t".join(("chr{}".format(chrom), str(gen_coords[start]), str(gen_coords[end]), str(gen_coords[max_dist_index]), str(compartments1[max_dist_index]), str(compartments2[max_dist_index]))))
			out.write("\n")
		out.close()

	with open("comp_peaks.bed", "w") as out:
		for peak in diff_peaks:
			start, end = peak
			out.write("\t".join(("chr{}".format(chrom), str(gen_coords[start]), str(gen_coords[end]))))
			out.write("\n")
		out.close()

if __name__ == "__main__":
	main()
