#! /usr/bin/env python

import random
from optparse import OptionParser

DEBUG = False

def dprint(str):
    if DEBUG:
        print str

printOps      = True
printState    = True
printFinal    = True

class bitmap:
    def __init__(self, size):
        self.size = size
        self.bmap = []
        for num in range(size):
            self.bmap.append(0)

    def alloc(self):
        for num in range(len(self.bmap)):
            if self.bmap[num] == 0:
                self.bmap[num] = 1
                return num
        return -1

    def free(self, num):
        assert(self.bmap[num] == 1)
        self.bmap[num] = 0

    def markAllocated(self, num):
        assert(self.bmap[num] == 0)
        self.bmap[num] = 1

    def dump(self):
        s = ''
        for i in range(len(self.bmap)):
            s += str(self.bmap[i])
        return s

class block:
    def __init__(self, ftype):
        assert(ftype == 'd' or ftype == 'f' or ftype == 'free')
        self.ftype = ftype
        # only for directories, properly a subclass but who cares
        self.dirUsed = 0
        self.maxUsed = 32
        self.dirList = []
        self.data    = ''

    def dump(self):
        if self.ftype == 'free':
            return '[]'
        elif self.ftype == 'd':
            rc = ''
            for d in self.dirList:
                # d is of the form ('name', inum)
                short = '(%s,%s)' % (d[0], d[1])
                if rc == '':
                    rc = short
                else:
                    rc += ' ' + short
            return '['+rc+']'
            # return '%s' % self.dirList
        else:
            return '[%s]' % self.data

    def setType(self, ftype):
        assert(self.ftype == 'free')
        self.ftype = ftype

    def addData(self, data):
        assert(self.ftype == 'f')
        self.data = data

    def getNumEntries(self):
        assert(self.ftype == 'd')
        return self.dirUsed

    def getFreeEntries(self):
        assert(self.ftype == 'd')
        return self.maxUsed - self.dirUsed

    def getEntry(self, num):
        assert(self.ftype == 'd')
        assert(num < self.dirUsed)
        return self.dirList[num]

    def addDirEntry(self, name, inum):
        assert(self.ftype == 'd')
        self.dirList.append((name, inum))
        self.dirUsed += 1
        assert(self.dirUsed <= self.maxUsed)

    def delDirEntry(self, name):
        assert(self.ftype == 'd')
        tname = name.split('/')
        dname = tname[len(tname) - 1]
        for i in range(len(self.dirList)):
            if self.dirList[i][0] == dname:
                self.dirList.pop(i)
                self.dirUsed -= 1
                return
        assert(1 == 0)

    def dirEntryExists(self, name):
        assert(self.ftype == 'd')
        for d in self.dirList:
            if name == d[0]:
                return True
        return False

    def free(self):
        assert(self.ftype != 'free')
        if self.ftype == 'd':
            # check for only dot, dotdot here
            assert(self.dirUsed == 2)
            self.dirUsed = 0
        self.data  = ''
        self.ftype = 'free'

class inode:
    def __init__(self, ftype='free', addr=-1, refCnt=1):
        self.setAll(ftype, addr, refCnt)

    def setAll(self, ftype, addr, refCnt):
        assert(ftype == 'd' or ftype == 'f' or ftype == 'free')
        self.ftype  = ftype
        self.addr   = addr
        self.refCnt = refCnt

    def incRefCnt(self):
        self.refCnt += 1

    def decRefCnt(self):
        self.refCnt -= 1

    def getRefCnt(self):
        return self.refCnt

    def setType(self, ftype):
        assert(ftype == 'd' or ftype == 'f' or ftype == 'free')
        self.ftype = ftype

    def setAddr(self, block):
        self.addr = block

    def getSize(self):
        if self.addr == -1:
            return 0
        else:
            return 1

    def getAddr(self):
        return self.addr

    def getType(self):
        return self.ftype

    def free(self):
        self.ftype = 'free'
        self.addr  = -1
        

class fs:
    def __init__(self, numInodes, numData):
        self.numInodes = numInodes
        self.numData   = numData
        
        self.ibitmap = bitmap(self.numInodes)
        self.inodes  = []
        for i in range(self.numInodes):
            self.inodes.append(inode())

        self.dbitmap = bitmap(self.numData)
        self.data    = []
        for i in range(self.numData):
            self.data.append(block('free'))
    
        # root inode
        self.ROOT = 0

        # create root directory
        self.ibitmap.markAllocated(self.ROOT)
        self.inodes[self.ROOT].setAll('d', 0, 2)
        self.dbitmap.markAllocated(self.ROOT)
        self.data[0].setType('d')
        self.data[0].addDirEntry('.',  self.ROOT)
        self.data[0].addDirEntry('..', self.ROOT)

        # these is just for the fake workload generator
        self.files      = []
        self.dirs       = ['/']
        self.nameToInum = {'/':self.ROOT}

    def dump(self):
        print 'inode bitmap ', self.ibitmap.dump()
        print 'inodes       ',
        for i in range(0,self.numInodes):
            ftype = self.inodes[i].getType()
            if ftype == 'free':
                print '[]',
            else:
                print '[%s a:%s r:%d]' % (ftype, self.inodes[i].getAddr(), self.inodes[i].getRefCnt()),
        print ''
        print 'data bitmap  ', self.dbitmap.dump()
        print 'data         ',
        for i in range(self.numData):
            print self.data[i].dump(),
        print ''
        print self.files
        print self.dirs
        print self.nameToInum

    def makeName(self):
        p = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'j', 'k', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
        return p[int(random.random() * len(p))]

    def inodeAlloc(self):
        return self.ibitmap.alloc()

    def inodeFree(self, inum):
        self.ibitmap.free(inum)
        self.inodes[inum].free()

    def dataAlloc(self):
        return self.dbitmap.alloc()

    def dataFree(self, bnum):
        self.dbitmap.free(bnum)
        self.data[bnum].free()
        
    def getParent(self, name):
        tmp = name.split('/')
        if len(tmp) == 2:
            return '/'
        pname = ''
        for i in range(1, len(tmp)-1):
            pname = pname + '/' + tmp[i]
        return pname

    def deleteFile(self, tfile):
        if printOps:
            print 'unlink("%s");' % tfile

        inum = self.nameToInum[tfile]
        assert(self.inodes[inum].getType() == 'f')

        dnum = self.inodes[inum].getAddr()
        if self.inodes[inum].getRefCnt() == 1:
            self.inodes[inum].free()
            self.data[dnum].free()
        else:
            self.inodes[inum].decRefCnt()

        
        pname = self.getParent(tfile)
        pinum = self.nameToInum[pname]
        pdnum = self.inodes[pinum].getAddr()
        self.inodes[pinum].decRefCnt()
        self.data[pdnum].delDirEntry(tfile)
        self.files.remove(tfile)
        self.nameToInum.pop(tfile)

    # YOUR CODE, YOUR ID
        # IF inode.refcnt ==1, THEN free data blocks first, then free inode, ELSE dec indoe.refcnt
        # remove from parent directory: delete from parent inum, delete from parent addr
    # DONE

        # finally, remove from files list
        return 0

    def createLink(self, target, newfile, parent):

    # YOUR CODE, YOUR ID
        # find info about parent
        # is there room in the parent directory?
        # if the newfile was already in parent dir?
        # now, find inumber of target
        # inc parent ref count
        # now add to directory
    # DONE
	pinum = self.nameToInum[parent]
        pdatanum = self.inodes[pinum].getAddr()
	if self.data[pdatanum].getFreeEntries():
            tinum = self.nameToInum[target]
            if tinum < len(self.inodes) and tinum >= 0:
                self.inodes[pinum].incRefCnt()
                self.inodes[tinum].incRefCnt()
                pdata = self.inodes[pinum].getAddr()
                self.data[pdata].addDirEntry(newfile,tinum)
			
        return tinum

    def createFile(self, parent, newfile, ftype):
    # YOUR CODE, YOUR ID
        # find info about parent
        # is there room in the parent directory?
        # have to make sure file name is unique
        # find free inode
        # if a directory, have to allocate directory block for basic (., ..) info
        # now ok to init inode properly
        # inc parent ref count
        # and add to directory of parent
    # DONE
        print 'createFile(',
        print parent,
        print ', ' + newfile + ', ' + ftype + ')'
        pinum = self.nameToInum[parent]
        pdatanum = self.inodes[pinum].getAddr()
        free_count = self.data[pdatanum].getFreeEntries()
        if free_count <= 0:
            return -1
        if newfile in self.files:
            return -1
        inum = self.inodeAlloc()
        if inum == -1:
            return -1
        if ftype == 'f':
            self.inodes[inum].setAll(ftype, -1, 1)
            currfile = parent + '/' + newfile
 #           self.nameToInum[currfile] = inum
        else:
            datanum = self.dataAlloc()
            if datanum == -1:
                return -1
            self.inodes[inum].setAll(ftype, datanum, 2)
            self.data[datanum].setType('d')
            if parent == '/':
                currdir = parent + newfile
            else:
                currdir = parent + '/' + newfile
            self.data[datanum].addDirEntry('.', inum)
            self.data[datanum].addDirEntry('..', pinum)
#            self.nameToInum[currdir] = inum
        self.data[pdatanum].addDirEntry(newfile, inum)
        self.inodes[pinum].incRefCnt()
        return inum

   
