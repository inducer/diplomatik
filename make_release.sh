#! /bin/bash
VERSION=`cat VERSION`
DESTDIR=diplomatik-$VERSION

rm -Rf $DESTDIR
mkdir $DESTDIR
cp START start-diplomatik.bat README VERSION LICENSE-* *.py $DESTDIR
mkdir $DESTDIR/tex-templates
mkdir $DESTDIR/tex-templates/unibrief
cp -R tex-templates/*.tex $DESTDIR/tex-templates
cp -R tex-templates/unibrief/* $DESTDIR/tex-templates/unibrief
mkdir $DESTDIR/html-templates
cp html-templates/*.html $DESTDIR/html-templates
mkdir $DESTDIR/static
cp static/*.{html,css,png,gif} $DESTDIR/static
mkdir $DESTDIR/yaml
cp yaml/*.py $DESTDIR/yaml
mkdir -p $DESTDIR/example-data/data
cp -R example-data/version-tag $DESTDIR/example-data
cp -R example-data/data/* $DESTDIR/example-data/data
tar cfz $DESTDIR.tar.gz --owner=nobody --group=nogroup $DESTDIR

