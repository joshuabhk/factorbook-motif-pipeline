BEGIN{
	OFS="\t" ;
}

{
	sub(/jobs\/.*\.mm9\./, "" ); 
	sub(/\/top500\.center\.meme_out/, "") ;
	print ;
}
