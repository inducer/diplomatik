#! /bin/bash
VERSION=`cat VERSION`
DESTDIR=diplomatik-$VERSION

rm -Rf $DESTDIR
mkdir $DESTDIR
cp START start-diplomatik.bat VERSION LICENSE-* *.py $DESTDIR
mkdir $DESTDIR/tex-templates
cp tex-templates/*.tex $DESTDIR/tex-templates
mkdir $DESTDIR/html-templates
cp html-templates/*.html $DESTDIR/html-templates
mkdir $DESTDIR/static
cp static/*.{html,css} $DESTDIR/static
mkdir $DESTDIR/yaml
cp yaml/*.py $DESTDIR/yaml
mkdir $DESTDIR/example-data
cp example-data/* $DESTDIR/example-data
tar cfz $DESTDIR.tar.gz $DESTDIR

