#!/bin/bash

if [ $# -ge 4 ] ;
then
	#default variables
	#related to the path setting.
	dir=`pwd`
	fn=$1
	jobname=$fn
	i=$dir/$fn
	name=$fn

	#number of cpus to use.
	np=$2

	#genome database to use.
	genome=$3

	#peak normalization selection.
	normtype=$4 #summit center
	summitcol=$5 #if norm is "center" $5 value will be ignored!
else
	echo "Usage: $0 <spp_filename> <n_proc> <genome> <normalization_type> <peak summit column #>"
	exit 1;
fi 

sorting=0

#settings for temporary working directory
current_dir=`pwd`
save_dir="$current_dir"
temp_dir=`mktemp -d`

#project_dir=/home/kimb/projects/encode_gr_mm
project_dir="/home/kimb/factorbook_motif_pipeline"
bin_dir="$project_dir/bin"

######################################################
#db setting
#genome=hg19

motif_db="$project_dir/db/motif_databases"
gcPercentDir="$project_dir/db/$genome/gcPercent.window300/"
chromInfo="$project_dir/db/$genome/chromInfo"
twobit="$project_dir/db/$genome/2bit"
fa="$project_dir/db/$genome/fa"
######################################################

cd $temp_dir

echo starting dir $current_dir...
echo working in $temp_dir...
echo number of CPUs to be used $np...

echo "building symbolic link to the file $i"
echo ln -s $i ./
ln -s $i ./

echo "building $name\_summits.window150.bed"

#awk -F "\t" '{OFS="\t"; print $1,$2+$10-150,$2+$10+150,"peak_"++i,$7,$9}' $fn > $name\_summits.window150.bed
#The new code will produce bed4 format file.
if [ $normtype == "summit" ] ;
then 
	awk -F "\t" -v summitcol=$summitcol '{OFS="\t"; print $1,$2+$summitcol-150,$2+$summitcol+150,"peak_"++i,"0","0"}' $fn > $name\_summits.window150.bed ;
else 
	awk -F "\t" '{OFS="\t"; summit = sprintf( ($2+$3)*0.5 ) ; print $1,$2+summit-150,$2+summit+150,"peak_"++i,"0","0"}' $fn > $name\_summits.window150.bed ;
fi
	

bedClip $name\_summits.window150.bed $chromInfo $name\_summits.window150.clip.bed

######################################################
# top500 center 100bp
######################################################
if [ $sorting == 1 ] ;
then
	sort -k5gr -k6gr $name\_summits.window150.clip.bed | head -500 | cut -f1-4 > top500.summits.window150.bed
else
	cat $name\_summits.window150.clip.bed | head -500 | cut -f1-4 > top500.summits.window150.bed
fi

twoBitToFa $twobit top500.seqs -bed=top500.summits.window150.bed
fasta-center -len 100 -flank top500.seqs.flank < top500.seqs > top500.seqs.center
date +%Y%m%d%H%M%S
if [ $np -eq 1 ] 
then
	meme -oc top500.center.meme_out -nostatus top500.seqs.center -sf $name.top500.center -dna -mod zoops -nmotifs 5 -minw 6 -maxw 30 -revcomp
else
	mpirun -np $np meme_p -oc top500.center.meme_out -nostatus top500.seqs.center -sf $name.top500.center -dna -mod zoops -nmotifs 5 -minw 6 -maxw 30 -revcomp -p $np
fi

date +%Y%m%d%H%M%S
tomtom -verbosity 1 -oc top500.center.meme_tomtom_out -min-overlap 5 -dist pearson -evalue -thresh 0.1 -no-ssc top500.center.meme_out/meme.txt $motif_db/gr_paper_extended.meme $motif_db/JASPAR_CORE_2009.meme $motif_db/transfac.meme

rm $name\_summits.window150.bed top500.summits.window150.bed top500.seqs top500.seqs.center top500.seqs.flank #top500.seqs.center.shuffle #top500.seqs.center_w_bg


######################################################
#combine fimo_memechip.signalvalue.top501-1000.random
#fimo_memechip.signalvalue.top501-1000.random.peakless 600
#selecting which pass
######################################################
peak_count=`cat $fn | wc -l`
if [ $peak_count -gt 600 ];
then #for files more than 600 peaks
    headRest 500 $name\_summits.window150.clip.bed | head -500 | cut -f1-4 | bedtools nuc -fi $fa -bed stdin | grep -v "^#" | cut -f4,6 | awk '{ OFS="\t"; if($2*100<int($2*100)+0.5) { print $1,int($2*100)} else { print $1,int($2*100)+0.5}}' > top500-1000.gcPercent
    headRest 500 $name\_summits.window150.clip.bed | head -500 | cut -f1-4 > top500-1000.bed
else #for files less than 600 peaks
    cut -f1-4 $name\_summits.window150.clip.bed | bedtools nuc -fi $fa -bed stdin | grep -v "^#" | cut -f4,6 | awk '{ OFS="\t"; if($2*100<int($2*100)+0.5) { print $1,int($2*100)} else { print $1,int($2*100)+0.5}}' > top500-1000.gcPercent
    cut -f1-4 $name\_summits.window150.clip.bed > top500-1000.bed
fi

cat top500-1000.gcPercent | while read id gcp
do
	gcPercentBedGraph="${gcPercentDir}/gcPercent.window300.$gcp.bedGraph"
	bedtools intersect -a $gcPercentBedGraph -b $name\_summits.window150.clip.bed -wa -v > gcp
	for i in {1..100}
	do
		echo -e "$id.$i" >> tmp1
		randomLines -seed=$RANDOM gcp 1 stdout | cut -f1-3 >> tmp2 
	done
done

paste tmp2 tmp1 > top500-1000.sameGC.random.bed; rm tmp2 tmp1 
twoBitToFa $twobit top500-1000.sameGC.random.fa -bed=top500-1000.sameGC.random.bed
cp top500.center.meme_out/meme.txt ./ 
fimo -o top500-1000.sameGC.random.meme_fimo_out meme.txt top500-1000.sameGC.random.fa 

#source of the bug...
#cut -f1-4 $name\_summits.window150.clip.bed > top500-1000.bed

twoBitToFa $twobit top500-1000.fa -bed=top500-1000.bed
fimo -o top500-1000.meme_fimo_out meme.txt top500-1000.fa
rm meme.txt

#removing some header in old gr paper
#fnn=`echo $fn | sed 's/spp.idrOptimal.hg19.//;'`
#new code does not remove prefix!
fnn=$fn #`echo $fn | sed 's/spp.idrOptimal.hg19.//;'`

Rscript $bin_dir/fimo.top500-1000.random.summary.sge.R $fnn
#cp -rf *xTFBS* /home/wangj2/anearline/encode.paper/meme-chip.signalvalue/$fn/ 
#cp -rf top500-1000.sameGC.random.meme_fimo_out/fimo.txt /home/wangj2/anearline/encode.paper/meme-chip.signalvalue/$fn/$fn.top500-1000.sameGC.random.fimo.txt
#cp -rf top500-1000.meme_fimo_out/fimo.txt /home/wangj2/anearline/encode.paper/meme-chip.signalvalue/$fn/$fn.top500-1000.fimo.txt
######################################################


######################################################
#fimo_memechip.signalvalue.flanking.sh
######################################################
awk -F "\t" '{OFS="\t"; print $1,$2-300,$3+300,$4}' $name\_summits.window150.clip.bed > $name\_summits.window450.clip.bed
bedClip $name\_summits.window450.clip.bed $chromInfo tmp
twoBitToFa $twobit $fn\_summits.window450.clip.fa -bed=tmp
rm tmp
fasta-center -len 300 -flank seqs.flank < $fn\_summits.window450.clip.fa > seqs.center
cp top500.center.meme_out/meme.txt ./
fimo -o top500.center.meme.flanking.fimo_out meme.txt seqs.flank
rm meme.txt

#cp -r top500.center.meme.flanking.fimo_out/fimo.txt /home/wangj2/anearline/encode.paper/meme-chip.signalvalue/$fn/top500.center.meme.flanking.fimo.txt
#rm -rf $HOME/scratch/jobid_$JOB_ID/

#fimo run for plotting
cut -f1-4 ${name}_summits.window150.clip.bed > top500.bed #should be like this!!
twoBitToFa $twobit all.seqs.center -bed=top500.bed
cp top500.center.meme_out/meme.txt ./
fimo -o top500.center.meme_fimo_out meme.txt all.seqs.center

rm meme.txt all.seqs.center

mkdir -p $save_dir
cp -r * $save_dir
rm -rf $temp_dir
