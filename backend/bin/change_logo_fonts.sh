for i in jobs/*/top500.center.meme_out/meme.txt
do
	dir=`dirname $i`
	name=`basename $i`
	logo=`grep Multilevel $dir/$name | perl -ne 'chomp; split; @g=/(G)/g; @c=/(C)/g; @a=/(A)/g; @t=/(T)/g; if(@g>@c) { print "logo",++$i,".eps\t"} elsif(@g==@c && @a>@t) { print "logo",++$i,".eps\t";} else { print "logo_rc",++$i,".eps\t";}'`

	clean_name=`echo $dir | perl -pe 's/jobs\/(.*)\/top500.*/$1/'`
	echo -e "$clean_name\t$logo"
done 
