	args<-commandArgs(TRUE)
	i<-args[1]
	spp<-i
#	print(i)
#	if(i=="wgEncodeHaibTfbsGm12891Pu1Pcr1xAlnRep0"){ next }
#	spp<-gsub(".bam.*","",i)
#	info<-master[master$spp_filename==i,]
	print(i)

#	fl<-system(paste("wc -l /home/wangj2/anearline/encode_Jan2011/meme-chip.signalvalue/spp.optimal.",spp,"/spp.optimal.",spp,".top500-1000.fimo.txt | cut -f1 -d \" \"",sep=""),intern=T)
	fl<-system( "wc -l top500-1000.meme_fimo_out/fimo.txt | cut -f1 -d \" \"",intern=T)

	print(fl)
	if(as.numeric(fl)<=1) { next }
	fimo<-read.table("top500-1000.meme_fimo_out/fimo.txt", sep="\t")
	if(nrow(fimo)>0)
	{
		fimo<-data.frame(fimo[,1:2],apply(fimo,1,function(x) if(150 %in% seq(as.numeric(x[3]),as.numeric(x[4]))) { 0 } else { min(abs(as.numeric(x[4])-150),abs(as.numeric(x[3])-150)) }))
	}
	
	fl<-system( "wc -l top500-1000.sameGC.random.meme_fimo_out/fimo.txt | cut -f1 -d \" \"",intern=T)
	if(as.numeric(fl)<=1) { next }
	fimo.random<-read.table("top500-1000.sameGC.random.meme_fimo_out/fimo.txt",sep="\t")
	if(nrow(fimo.random)>0)
	{
		fimo.random<-data.frame(fimo.random[,1:2],apply(fimo.random,1,function(x) if(150 %in% seq(as.numeric(x[3]),as.numeric(x[4]))) { 0 } else { min(abs(as.numeric(x[4])-150),abs(as.numeric(x[3])-150)) }))
		fimo.random<-data.frame(fimo.random,t(apply(fimo.random,1,function(x) unlist(strsplit(as.character(x[2]),"\\."))))[,2])
	}

	for(j in seq(1,5,1))
	{
		motif<-as.data.frame(tapply(fimo[fimo[,1]==j,3],fimo[fimo[,1]==j,2],min))
		sample.table<-matrix(0,1,100)
		for(k in seq(1,100,1))
		{
			motif.random<-as.data.frame(tapply(fimo.random[fimo.random[,1]==j & fimo.random[,4]==k,3],fimo.random[fimo.random[,1]==j & fimo.random[,4]==k,2],min))	
			sample.table[1,k]<-sum(!is.na(motif.random))
		}
		write.table(data.frame(spp,j,sum(!is.na(motif)),sample.table),paste("fimo.top500-1000.pct.summary.100samples.xTFBS.clean",sep=""),col.name=F,row.names=F,sep="\t",quote=F,append=T)
	}
