from fac import *
from types import *
import time

# reinitialize FAC
def reinit(m = 0):
    Reinit(m)

    return

# the index of n-th shell in a complex
def get_index(n, complex):
    for i in range(len(complex)):
        if (complex[i][0] == n):
            return i
        elif (complex[i][0] > n):
            return -i-1
        
    return -i-2


# a configuration complex
class COMPLEX:
    def __init__(self, nele = 0):
        self.complex = []
        self.nrec = 0
        self.name = ' '

        if (nele > 0):
            self.set_ground(nele)
            self.set_name()
            
        return

    def set_name(self, c = 0):
        if (type(c) == StringType):
            self.name = c
            return

        cname = 0
        for s in self.complex:
            if (type(cname) == IntType):
                cname = '%d*%d'%(s[0], s[1])
            else:
                cname = cname + ' %d*%d'%(s[0], s[1])
        if (type(cname) == IntType):
            cname = 'bare'
            
        self.name = cname
        
        return

    def set_ground(self, nelectrons):
        n = 1
        nele = nelectrons
        g = []
        while (nele > 0):
            nqm = 2*n*n
            if (nele < nqm):
                g.append((n, nele))
            else:
                g.append((n, nqm))
            nele = nele - nqm
            n = n+1

        self.complex = g
        
        return 

    def set_excited(self, i0, i1, cbase):
        base = cbase.complex
        if (i0 >= i1):
            return -1
        i = get_index(i0, base)
        if (i < 0):
            return -1
        j = get_index(i1, base)
        ex = base[:]
        if (j >= 0):
            nq1 = ex[j][1]
            if (nq1 == 2*i1*i1):
                return 0
            else:
                ex[j] = (i1, nq1+1)
        else:
            j = -j - 1
            ex.insert(j, (i1, 1))

        nq0 = ex[i][1]
        if (nq0 == 1):
            ex.remove(ex[i])
        else:
            ex[i] = (i0, nq0-1)
    
        self.complex = ex
        self.set_name()

        return 0

    def set_ionized(self, i0, cbase):
        base = cbase.complex
        i = get_index(i0, base)
        if (i < 0):
            return -1
        ion = base[:]
        nq0 = ion[i][1]
        if (nq0 == 1):
            ion.remove(ion[i])
        else:
            ion[i] = (i0, nq0-1)

        self.complex = ion
        self.set_name()
        
        return 0

    def set_recombined(self, i0, cbase):
        self.set_name(cbase.name)
        self.nrec = i0
        self.complex = ([cbase.name], i0)
        
        return 0
    

# a group of complexes
class CGROUP:
    def __init__(self, type):
        self.cgroup = []
        self.type = type

        return

    def add_complex(self, complex):
        self.cgroup.append(complex)

        return

    def complex_names(self):
        cname = []
        for c in self.cgroup:
            cname.append(c.name)

        return cname

    def complexes(self):
        c = []
        for a in self.cgroup:
            c.append(a.complex)

        return c
    

# a generic atomic ion
class ATOM:    
    def __init__(self, nele, asym = 0):
        self.nele = nele

        self.nele_max = [0, 2, 10, 28]
        
        self.grd_complex = COMPLEX(nele)
        self.exc_complex = []
        self.ion_complex = CGROUP('ion')
        self.rec_complex = []

        self.angz_cut0 = 1E-3
        
        if (self.nele <= self.nele_max[1]):
            self.n_shells = 1
            self.nexc_max = [7, 7]
            self.nexc_rec = [0, 0]
            self.nrec_max = [30, 10]
            self.rec_pw_max = [10, 8]
            self.n_decay = [11, 0]
            self.angz_cut1 = 1E-3
        elif (self.nele <= self.nele_max[2]):
            self.n_shells = 2
            self.nexc_max = [5, 4, 5]
            self.nexc_rec = [7, 0, 0]
            self.nrec_max = [30, 8, 10]
            self.rec_pw_max = [10, 8, 8]
            self.n_decay = [11, 0, 0]
            self.angz_cut1 = 1E-2
        elif (self.nele <= self.nele_max[3]):
            self.n_shells = 3
            self.nexc_max = [3, 7, 5, 0]
            self.nexc_rec = [0, 0, 0, 0]
            self.nrec_max = [0, 10, 8, 0]
            self.rec_pw_max = [10, 8, 8, 8]
            self.n_decay = [0, 0, 0, 0]
            self.angz_cut1 = 1E-2

        if (type(asym) == StringType):
            self.set_atom(asym)
            
        return

    
    def set_atom(self, asym):
        self.asym = asym
        self.bfiles = {'en': '%s%02db.en'%(asym, self.nele),
                       'tr': '%s%02db.tr'%(asym, self.nele),
                       'ce': '%s%02db.ce'%(asym, self.nele),
                       'rr': '%s%02db.rr'%(asym, self.nele),
                       'ai': '%s%02db.ai'%(asym, self.nele),
                       'ci': '%s%02db.ci'%(asym, self.nele)}
        
        self.afiles = {'en': '%s%02da.en'%(asym, self.nele),
                       'tr': '%s%02da.tr'%(asym, self.nele),
                       'ce': '%s%02da.ce'%(asym, self.nele),
                       'rr': '%s%02da.rr'%(asym, self.nele),
                       'ai': '%s%02da.ai'%(asym, self.nele),
                       'ci': '%s%02da.ci'%(asym, self.nele)}

        return


    def add_excited(self, n0, n1, base = 0):
        if (type(base) == IntType):
            base = self.grd_complex

        n1.sort()
        
        cg = CGROUP('exc')
        for i1 in n1:
            ex = COMPLEX()
            if (ex.set_excited(n0, i1, base) == 0):
                cg.add_complex(ex)

        self.exc_complex.append(cg)
        
        return
    

    def add_ionized(self, n0, base = 0):
        if (type(base) == IntType):
            base = self.grd_complex
        
        ion = COMPLEX()
        ion.set_ionized(n0, base)
        self.ion_complex.add_complex(ion)

        return


    def add_recombined(self, n0, base = 0):
        if (type(base) == IntType):
            base = self.ion_complex.cgroup[0]

        n0.sort()
        
        cg = CGROUP('rec')
        for i0 in n0:
            rec = COMPLEX()
            if (rec.set_recombined(i0, base) == 0):
                cg.add_complex(rec)

        self.rec_complex.append(cg)
        
        return


    def run_tr_ce(self, a, b, c, d, tr = [-1], ce = 1):
        if (type(a) == StringType or type(a) == IntType):
            low = [a]
        else:
            low = a
        if (type(b) == StringType or type(b) == IntType):
            up = [b]
        else:
            up = b
            
        for m in tr:
            s = 'TR: %s -> %s %d'%(str(a), str(b), m)
            Print(s)
            TransitionTable(self.bfiles['tr'], low, up, m)

        if (ce != 0):
            if (type(c) == StringType or type(c) == IntType):
                low = [c]
            else:
                low = c
            if (type(d) == StringType or type(d) == IntType):
                up = [d]
            else:
                up = d
            s = 'CE: %s -> %s'%(str(c), str(d))
            Print(s)
            CETable(self.bfiles['ce'], low, up)

        Reinit(radial = 1, excitation = 1, structure = 1)
        
        return


    def run_ci_rr(self, a, b, c, d, ci = 1, rr = 1):
        if (rr != 0):
            if (type(c) == StringType or type(c) == IntType):
                low = [c]
            else:
                low = c
            if (type(d) == StringType or type(d) == IntType):
                up = [d]
            else:
                up = d
            s = 'RR: %s -> %s'%(c, d)
            Print(s)
            
            RRTable(self.bfiles['rr'], low, up)
            
            SetPEGrid(0)
            SetUsrPEGrid(0)
            SetRRTEGrid(0)
            
        if (ci != 0):
            if (type(a) == StringType or type(a) == IntType):
                low = [a]
            else:
                low = a
            if (type(b) == StringType or type(b) == IntType):
                up = [b]
            else:
                up = b
            s = 'CI: %s -> %s'%(a, b)
            Print(s)
            CITable(self.bfiles['ci'], low, up)


        if (ci != 0 or rr != 0):
            Reinit(radial = 1, recombination = 1,
                   ionization = 1, structure = 1)
        
        return


    def run_ai(self, a, b, k):
        s = 'AI: %s -> %s'%(a, b)
        Print(s)
        if (type(a) == StringType or type(a) == IntType):
            low = [a]
        else:
            low = a
        if (type(b) == StringType or type(b) == IntTaype):
            up = [b]
        else:
            up = b

        AITable(self.bfiles['ai'], low, up, k)

        Reinit(radial = 1, recombination = 1, structure = 1)
        
        return
    

    def run_en(self):        
        SetAtom(self.asym)
        SetAngZCut(self.angz_cut0)
        
        OptimizeRadial([self.grd_complex.name])

        c = self.exc_complex[0].complex_names()
        # ground and the first excited complex are interacting
        Print('Structure: ground complex')
        if (len(c) > 0):
            g = [self.grd_complex.name, c[0]]
        else:
            g = [self.grd_complex.name]
        Structure(self.bfiles['en'], g)

        Print('Structure: excited complexes')
        for a in c[1:]:
            Structure(self.bfiles['en'], [a])

        for b in self.exc_complex[1:]:
            c = b.complex_names()
            for a in c:
                if (a == ' '):
                    continue
                Structure(self.bfiles['en'], [a])

        Print('Structure: ionized complexes')
        c = self.ion_complex.complex_names()
        for a in c:
            Structure(self.bfiles['en'], [a])

        Print('Structure: recombined complexes')
        for i in range(len(self.rec_complex)):
            b = self.rec_complex[i]
            c = b.complex_names()
            SetRecPWOptions(self.rec_pw_max[i])
            SetRecSpectator(self.nexc_max[i])
            for i in range(len(c)):
                n = b.cgroup[i].nrec
                RecStates(self.bfiles['en'], [c[i]], n)

        return


    def run_tr_ce_all(self):
        # ground - ground, CE, E1 and M1, E2, M2.
        # K shell ions only have one level in the ground complex
        if (self.n_shells > 1):
            a = self.grd_complex.name
            self.run_tr_ce(a, a, a, a, tr = [-1, 1, -2, 2], ce = 1)

        # ground - excited, CE, E1 and M1.
        # include E2, M2, for the first excited complex
        a = self.grd_complex.name
        for k in range(self.n_shells):
            exc = self.exc_complex[k].complex_names()
            SetAngZCut(self.angz_cut0)
            for i in range(len(exc)):
                if (k == 0 and i == 0):
                    tr = [-1, 1, -2, 2]
                else:
                    tr = [-1, 1]
                if (i > 1):
                    SetAngZCut(self.angz_cut1)
                b = exc[i]
                if (b == ' '):
                    continue
                if (i == 0):
                    c = a
                else:
                    if (self.n_shells == 1):
                        c = a
                    else:
                        c = 0
                self.run_tr_ce(a, b, c, b, tr = tr, ce = 1)

        # ground - recombined, CE, E1.
        SetAngZCut(self.angz_cut1)
        a = self.grd_complex.name
        for k in range(self.n_shells):
            rec = self.rec_complex[k].cgroup
            for i in range(len(rec)):
                b = rec[i]
                if (b.nrec > self.nexc_rec[k]):
                    break
                b = b.complex
                self.run_tr_ce(a, b, 0, b, tr = [-1], ce = 1)

        # excited - excited
        for k in range(len(self.exc_complex)):
            exc1 = self.exc_complex[k].complex_names()
            for i in range(len(exc1)):
                a = exc1[i]
                if (a == ' '):
                    continue
                for m in range(len(self.exc_complex)):
                    if (m < k):
                        continue
                    exc2 = self.exc_complex[m].complex_names()
                    for j in range(len(exc2)):
                        b = exc2[j]
                        if (b == ' '):
                            continue
                        if (m == k and j < i):
                            continue
                        if (m != 0):
                            if (m == k):
                                if (j != 0):
                                    continue
                            else:
                                if (m == self.n_shells):
                                    if (k != 0):
                                        continue
                                    if (i != 0 and j != i):
                                        continue
                                else:
                                    if (j != i+m-k):
                                        continue
                        ce = 0
                        tr = [-1]
                        if (k == 0 and i == 0):
                            tr = [-1, 1]
                        if (self.n_shells == 1):
                            if (k == 0 and i == 0 and j <= 2):
                                ce = 1
                        self.run_tr_ce(a, b, a, b, tr = tr, ce = ce)
                        
        return

    
    def run_ci_rr_all(self):
        SetAngZCut(self.angz_cut0)
        # CI and PI from ground
        ion = self.ion_complex.complex_names()    
        a = self.grd_complex.name
        for b in ion[0:self.n_shells]:
            self.run_ci_rr(a, b, a, b, ci = 1, rr = 1)

        # RR onto ground to form excited states
        for a in self.exc_complex[0].complex_names():
            b = ion[0]
            if (self.n_shells == 1):
                ci = 1
            else:
                ci = 0
            self.run_ci_rr(a, b, a, b, ci = ci, rr = 1)

        # RR onto ground to form recombined states
        c = self.rec_complex[0].complex_names()
        for i in range(len(c)):
            b = ion[0]
            n = self.rec_complex[0].cgroup[i].nrec
            a = ([c[i]], n)
            self.run_ci_rr(a, b, a, b, ci = 0, rr = 1)
            
        return

    
    def run_dr_all(self):
        SetAngZCut(self.angz_cut0)
        ion = self.ion_complex.complex_names()   
        for k in range(len(self.rec_complex)):
            s = 'Channel %d'%(k)
            Print(s)
            if (k > 0 or (k == 0 and self.n_shells > 1)):
                c = self.exc_complex[k].complex_names()
                for a in c:
                    if (a == ' '):
                        continue
                    if (k == 0):
                        b = ion[0]
                        self.run_ai(a, b, k)
                    else:
                        for b in ion[0:k]:
                            self.run_ai(a, b, k)
                
            c = self.rec_complex[k].complex_names()
            for i in range(len(c)):
                n = self.rec_complex[k].cgroup[i].nrec
                a = ([c[i]], n)
                SetAngZCut(self.angz_cut0)
                if (k > 0 or (k == 0 and self.n_shells > 1)):
                    if (k == 0):
                        b = ion[0]
                        self.run_ai(a, b, k)
                    else:
                        for b in ion[0:k]:
                            self.run_ai(a, b, k)
                    
                if (k == 0):
                    self.run_tr_ce(a, a, 0, 0, tr = [-1], ce = 0)
                    b = self.grd_complex.name
                    if (n > self.nexc_rec[k]):
                        self.run_tr_ce(b, a, 0, 0, tr = [-1], ce = 0)
                    SetAngZCut(self.angz_cut1)
                    for b in self.exc_complex[0].complex_names():
                        self.run_tr_ce(b, a, 0, 0, tr = [-1], ce = 0)
                    for b in self.rec_complex[0].cgroup:
                        if (b.nrec < n and b.nrec <= self.n_decay[0]):
                            self.run_tr_ce(b.complex, a, 0, 0,
                                           tr = [-1], ce = 0)
                else:
                    for t in range(0, k):
                        d = self.exc_complex[t].cgroup
                        b = 0
                        for j in range(len(d)):
                            try:
                                if (d[j].complex[-1][0] == n):
                                    b = d[j].name
                                    break
                            except:
                                continue
                            
                        if (type(b) == IntType):
                            d = self.rec_complex[t].cgroup
                            for j in range(len(d)):
                                if (d[j].nrec == n):
                                    b = ([ion[t]], n)
                                    break
                        if (type(b) != IntType):
                            self.run_tr_ce(b, a, 0, 0, tr = [-1], ce = 0)
                    
                    if (n <= self.n_decay[k]):
                        SetAngZCut(self.angz_cut0)
                        
                        if (k == self.n_shells):
                            b = self.exc_complex[0].cgroup[0].name
                            self.run_tr_ce(b, a, 0, 0, tr = [-1], ce = 0)
                        else:
                            b = self.grd_complex.name
                            if (n > self.nexc_rec[k]):
                                self.run_tr_ce(b, a, 0, 0, tr = [-1], ce = 0)
                        
                        if (self.nele == self.nele_max[self.nshells]):
                            b = self.exc_complex[k].cgroup[1].name
                        else:
                            b = self.exc_complex[k].cgroup[0].name
                        self.run_tr_ce(b, a, 0, 0, tr = [-1], ce = 0)
                        

        return
    
    
    def print_table(self, type = [], v = 0):
        if (v != 0):
            MemENTable(self.bfiles['en'])

        for t in type:
            PrintTable(self.bfiles[t], self.afiles[t], v)
            
        return
  

    def set_configs(self):
        n = range(1, self.n_shells+1)
        n.reverse()
        nexc = self.nexc_max
        nrec = self.nrec_max
        for i in n:
            j = self.n_shells - i
            self.add_excited(i, range(nexc[j]+1))
            self.add_ionized(i)
            b = self.ion_complex.cgroup[j]
            self.add_recombined(range(nexc[j]+1, nrec[j]+1), b)

        if (self.nele > self.nele_max[self.n_shells-1]+1):
            if (len(self.exc_complex[0].cgroup) > 0):
                b = self.exc_complex[0].cgroup[0]
                j = self.n_shells
                self.add_excited(j, range(nexc[j]+1), b)
                self.add_ionized(j, b)
                b = self.ion_complex.cgroup[j]
                self.add_recombined(range(nexc[j]+1, nrec[j]+1), b)
            
        # set up configurations
        c = self.grd_complex.name
        s = 'adding complex: %s'%(str(c))
        Print(s)
        Config(c, group = c)
            
        for cg in self.exc_complex:
            for c in cg.complex_names():
                if (c == ' '):
                    continue
                s = 'adding complex: %s'%(str(c))
                Print(s)
                Config(c, group = c)
                
        cg = self.ion_complex.complex_names()
        for c in cg:
            s = 'adding complex: %s'%(str(c))
            Print(s)
            if (c == 'bare'):
                Config('', group = c)
            else:
                Config(c, group = c)
 
        return


    def run_fac(self):
        start = time.time()
        start0 = start

        # solve the structure
        s = 'EN...'
        Print(s)
        self.run_en()        
        stop = time.time()
        s = 'Done %10.3E s'%(stop-start)
        print s

        # transition rates and collisional excitation
        start = stop  
        s = 'TR and/or CE...'
        Print(s)  
        self.run_tr_ce_all() 
        stop = time.time()
        s = 'Done %10.3E s'%(stop-start)
        print s

        # CI and/or RR
        start = stop
        s = 'CI and/or RR...'
        Print(s)
        self.run_ci_rr_all()
        stop = time.time()
        s = 'Done %10.3E s'%(stop-start)
        print s 

        start = stop 
        s = 'DR...'
        Print(s)
        self.run_dr_all()
        stop = time.time()
        s = 'Done %10.3E s'%(stop-start)
        print s

        s = 'Total Time: %10.3E s'%(stop-start0)
        print s

        return


def atomic_data(nele, asym, iprint = -1):
    if (type(asym) == StringType):
        a = [asym]
    else:
        a = asym

    if (type(nele) == IntType):
        n = [nele]
    else:
        n = nele

    for m in n:
        atom = ATOM(m)
        atom.set_configs()
        for b in a:
            s = 'NELE = %d'%m
            Print(s)
            s = 'ATOM = %s'%b
            z = ATOMICSYMBOL.index(b.lower())
            s = '%s, Z = %d'%(s, z)
            if (z < 1.5*m):
                Print('%s, skipping'%s)
                continue
            Print(s)
            atom.set_atom(b)
            atom.run_fac()
            if (iprint >= 0):
                atom.print_table(['en', 'tr', 'ce', 'rr', 'ai', 'ci'], iprint)
                
            Reinit(1)

        Reinit(0)

    return