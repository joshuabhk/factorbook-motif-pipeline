#!/bin/bash
fn=$1
tmpfn=`mktemp -p /tmp/`
sed 's/Helvetica-Bold/Helvetica/g' $fn > $tmpfn
mv $tmpfn $fn
