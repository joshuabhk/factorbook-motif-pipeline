#!/usr/bin/perl

open in,"test.xml";
while(<in>)
{
	if(/<text  id='33' string='3'/)
	{
		s/charpath/text/;
		s/string='3'/string='0'/;
	}
	if(/<text  id='36' string='3'/)
	{
		s/charpath/text/;
		s/string='3'/string='1'/;
	}
	if(/<text  id='39' string='3'/)
	{
		s/charpath/text/;
		s/string='3'/string='2'/;
	}
	print $_;	
}
close(in);

