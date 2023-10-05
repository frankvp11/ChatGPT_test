

import numpy as np


class Solver():
    def __init__(self, matrix):
        self.matrix = matrix



    def reduced_row_echelon_form(self, precision=7, GJ=False):
        mat = np.array(self.matrix, dtype=np.float64)
        m,n = mat.shape
        p,t = precision, 1e-1**precision
        A = np.around(mat.astype(float).copy(),decimals=p )
        if GJ:
            A = np.hstack((A,np.identity(n)))
        pcol = -1 #pivot colum
        for i in range(m):
            pcol += 1
            if pcol >= n : break
            #pivot index
            pid = np.argmax( abs(A[i:,pcol]) )
            #Row exchange
            A[i,:],A[pid+i,:] = A[pid+i,:].copy(),A[i,:].copy()
            #pivot with given precision
            while pcol < n and abs(A[i,pcol]) < t:
                pcol += 1
                if pcol >= n : break
                #pivot index
                pid = np.argmax( abs(A[i:,pcol]) )
                #Row exchange
                A[i,:],A[pid+i,:] = A[pid+i,:].copy(),A[i,:].copy()
            if pcol >= n : break
            pivot = float(A[i,pcol])
            for j in range(m):
                if j == i: continue
                mul = float(A[j,pcol])/pivot
                A[j,:] = np.around(A[j,:] - A[i,:]*mul,decimals=p)
            A[i,:] /= pivot
            A[i,:] = np.around(A[i,:],decimals=p)
            
        if GJ:
            return A[:,:n].copy(),A[:,n:].copy()
        else:
            return A   
    
    def determinant(self):
        return np.linalg.det(np.array(self.matrix))


    def eig(self):
        return np.linalg.eig(np.array(self.matrix))