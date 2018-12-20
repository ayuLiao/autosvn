AutoSVN

## Intro

auto update the file to SVN.

autosvn has different code, one is use shell , other is use python.

Shell code is easy. Just SVN common process.

Python code is commit SVN when files size more than 10M  which add commit space.

## Use

shell code

```
sh autosvn.sh your_origin_file_path your_target_path svn_url svn_username svn_password 0/1
```

0 --> don't unzip the file
1 --> unzip the file

python code

```
python autosvn.py -s your_origin_file_path -t your_target_path -svnpath your_svn_url -un svn_username -ps svn_password -unzip True/False
```
if -unzip True, will un zip file to target path.


Enjoy code.
