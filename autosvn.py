#coding:utf-8
import os
import commands
import Queue
import shutil
import zipfile
import tarfile
import time
import functools
import hashlib
import traceback

q = Queue.PriorityQueue()
errordict = {}


def speed_time(func):
    @functools.wraps(func)
    def print_time(*args, **kwargs):
        func_name = func.__name__
        t0 = time.time()
        res = func(*args, **kwargs)
        t1 = time.time()
        print('%s run time is (%s), the res is (%s)' % (func_name, t1 - t0, res))

    return print_time


def md5(name):
    md5 = hashlib.md5(name)
    return md5.hexdigest()

def errnum(error):
    if errordict.get(md5(error),''):
        errordict[md5(error)] += 1
    else:
        errordict[md5(error)] = 1
    return errordict[md5(error)]



class Job(object):

    def __init__(self, fsize, filepath):
        self.fsize = fsize
        self.filepath = filepath
        # print("filepath: ", filepath)
        return

    # customize <, =, >
    def __cmp__(self, other):
        return cmp(self.fsize, other.fsize)

def execshell(shell,path, cd=True):
    if cd:
        cdshell = 'cd {path}'.format(path=path)
        shell = cdshell + ' && ' + shell
    exit_status, output = commands.getstatusoutput(shell)
    print(exit_status, output)
    return exit_status, output


def status(path):
    shell = 'svn status'
    exit_status,output = execshell(shell, path)
    if exit_status == 0:
        print('success')
        return output.split('\n')
    else:
        print('fail')
        print(output)


def commit(tag,path, i=0):
    shell = 'svn commit -m {tag}'.format(tag=tag)
    _,output = execshell(shell,path)
    if 'svn: Commit failed' in output and i<3:
        i += 1
        commit(tag,path,i)
    if 'svn: Commit failed' in output and i > 3:
        print(output)
        print('\n')


def checkout(path, svnpath, username, password):
    shell = 'svn checkout {ippath} --username={username} --password={password}'.format(
        ippath = svnpath, username = username, password = password
    )
    execshell(shell, os.path.dirname(path[:-1]))

def update(path):
    shell = 'svn update'
    execshell(shell,path)

def revert(path):
    '''
    revert svn
    --depth=infinity . will revert the all folder
    :param path:
    :return:
    '''
    shell = 'svn revert --depth=infinity .'
    execshell(shell, path)

def add(filepath,path):
    '''
    add file in svn pending submission space
    :param filepath: file path which file need add svn
    :param path: root path. Add svn will recursive add, if recursive the root path then return the program
    :return:
    '''
    # add file , --non-recursive will just add this file will not recursive add all file which in this folder
    if '$' in filepath:
        nfilepath = filepath.replace('$','\$')
        shell = 'svn add --non-recursive {path}'.format(path=nfilepath)
    elif ' ' in filepath:
        nfilepath = filepath.replace(' ', '\ ')
        shell = 'svn add --non-recursive {path}'.format(path=nfilepath)
    else:
        shell = 'svn add --non-recursive {path}'.format(path=filepath)
    _, output = execshell(shell, path)

    # the file is not exist, svn can't find this file
    if 'W150002' in output and 'but is missing' in output:
        return

    if 'W150002' in output:
        print(shell)
        # This node is already in svn, can't add agent
        return

    elif 'W155010' in output or 'E155010' in output:
        if errnum(output) > 8:
            return
        # This node is not didn't find， add the father path
        if filepath == path:
            return
        # add father path, then add this path again
        add(os.path.dirname(filepath), path)
        add(filepath, path)


def get_filesize(fpath):
    filepath = fpath.encode('utf-8')
    fsize = os.path.getsize(filepath)
    return fsize


def dirlist(path):
    '''
    Put the fold all files in queue
    :param path: path
    :return:
    '''

    # remove the dir which name is '.' beginning
    filelist = [dir for dir in os.listdir(path) if not dir.startswith('.')]
    for filename in filelist:
        filepath = os.path.join(path, filename)
        if os.path.isdir(filepath):
            dirlist(filepath)
        q.put(Job(get_filesize(filepath), filepath))



def getstllist(path):
    '''
    Get the file which need add to svn
    ? --> SVN no manager file, need add in svn space
    :param path:
    :return:
    '''
    stlist = status(path)
    # the status has ? is the svn no management
    fplist = [fp.split('?')[-1].strip() for fp in stlist if '?' in fp]
    for fp in fplist:
        if os.path.isdir(path+fp):
            # Get new file which need add in svn space
            dirlist(path+fp)
        try:
            q.put(Job(get_filesize(path+fp), path+fp))
        except:
            print('Error path: ',path, fp)
            print(traceback.print_exc())


def isdiremtpy(path):
    if not os.path.exists(path):
        return True
    filelist = [dir for dir in os.listdir(path) if not dir.startswith('.')]
    if len(filelist):
        return False
    return True


def un_zip(path, target_path, unzipfiles=[], ):
    '''
    Decompression file to target path，
    able decompression zip file and tar.gz file
    :param path: Origin Zip File path
    :param target_path: un zip file path , the zip file will unzip for here
    :param unzipfiles: some situation just need un zip some file, use unzipfiles[list type] designation the file
    '''
    names = [None,]
    if zipfile.is_zipfile(path): # zip
        zip_file = zipfile.ZipFile(path)
        names = zip_file.namelist()
        if len(unzipfiles):
            for file_name in names:
                newfiles = [file for file in unzipfiles if file in file_name]
                if len(newfiles):
                    zip_file.extract(file_name, target_path)
        else:
            for file_name in names:
                zip_file.extract(file_name, target_path)
        zip_file.close()

    if tarfile.is_tarfile(path): # tar.gz tar
        tar = tarfile.open(path, "r:gz")
        names = tar.getnames()
        if len(unzipfiles):
            for file_name in names:
                newfiles = [file for file in unzipfiles if file in file_name]
                if len(newfiles):
                    tar.extract(file_name, target_path)
        else:
            for file_name in names:
                tar.extract(file_name, target_path)
        tar.close()
    return target_path, names[0]


def move(path, unzippath):
    # copy the new file to parent path, if exist overwrite
    shell = 'cd {path} && cp -rf * ../'.format(path=path+unzippath)
    exit_status, output = commands.getstatusoutput(shell)
    if exit_status == 0:
        # del old file
        shutil.rmtree(path+unzippath)
        print('success')
    else:
        print('fail')
        print(output)


@speed_time
def main(path, filepath, svnpath, username, password, unzip=False):
    if isdiremtpy(path):
        checkout(path, svnpath, username, password)
    else:
        revert(path)
        update(path)

    if unzip:
        # unzip file
        _, unzipname = un_zip(filepath,path)
        # move the file to father path
        move(path,unzipname)
    # get file list which need add to svn space
    getstllist(path)

    fsize = 10*1024*1024 # 10 M
    addsize = 0
    while not q.empty():
        next_job = q.get()
        size = next_job.fsize
        addsize += size
        add(next_job.filepath, path)
        if addsize >= fsize or q.empty():
            commit('version', path)
            addsize = 0
            print('commit file queue: [%s]'%str(q.qsize()))

    print('svn commit finish')


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Manual to this python script')
    parser.add_argument('-s', type=str, default='', help='src path, which path is svn workplace')
    parser.add_argument('-t', type=str, default='', help='target path, which the file you want to add svn')
    parser.add_argument('-svnp', type=str, default='', help='SVN URL, like svn://xxx.xxx.xxx')
    parser.add_argument('-un', type=str, default='', help='SVN user name')
    parser.add_argument('-ps', type=str, default='', help='SVN user password')
    parser.add_argument('-unzip', type=bool, default=False, help='did you want to unzip the file')
    args = parser.parse_args()

    path = args.s
    tpath = args.t
    svnpath = args.svnp
    username = args.un
    password = args.ps
    unzip = args.unzip


    if not path.endswith('/'):
        path = path + '/'
    main(path, tpath,svnpath, username, password, unzip)