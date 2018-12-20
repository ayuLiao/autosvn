#!/bin/bash

# Have to use the full path
path=$1
tpath=$2
svnurl=$3
username=$4
password=$5
isunzip=$6

# commit all the change
svncommit(){
    echo svncommit running
    start1=`date +%s`
    # svn add the new file
    svn status | awk '{if ($1 == "?") {print($2)}}' | xargs svn add
#    svn add *
    end1=`date +%s`
    echo "start1 and end1 running time is : ${start1}---${end1}"

    start2=`date +%s`
    svn commit -m 'add files'
    end2=`date +%s`
    echo "start2 and end2 running time is : ${start2}---${end2}"
}

# unzip cgame , get the agent folder and zip the new file
un_zip(){
    unzip ${tpath} -d ${path}
    zipname=${tpath##*/}
    zipname=${zipname%.*}
    cd ${path}
    cd ${zipname}
    cp -rf * ../
    rm -rf *
    cd ../
    mv agent ${zipname}
    zip -q -r ${zipname}.zip ${zipname}
    rm -rf ${zipname}
    rm -rf agent
    agent=../agent/
    if [ ! -d ${agent} ]; then
        mkdir ${agent}
    fi
    mv ${zipname}.zip ${agent}
}


if [ ! -d ${path} ]; then
    cd `dirname ${path}`
    svn checkout ${svnurl} --username=${username} --password=${password}
    cd ${path}
else
    cd ${path}
    count=`ls ${path}|wc -w` # the folder have file num
    if [ "$count" > "0" ]; then
        svn revert --depth=infinity .
        svn update
    else
        svn checkout ${svnurl} --username=${username} --password=${password}
    fi
fi


if [ "$isunzip" = 1 ]; then
    # unzip the file and move to the target path
    un_zip
fi


# add the new file in svn space, then commit the file
svncommit




