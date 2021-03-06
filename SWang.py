#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: zhshang
"""
import numpy as np
import matplotlib.pyplot as plt

L = 10
ESTEP = 1000
STEP = 10000

J = 1 # J>0 to make it ferromagnetic

# Intitialize the Ising Network
def Init():
    #return np.random.rand(L, L)*2*np.pi
    return np.ones([L, L])

# periodic neighbor
def next(x):
    if x == L-1:
        return 0
    else:
        return x+1

# construct the bond lattice
def FreezeBonds(Ising,T):
    freezProb = 1 - np.exp(-2 * J / T)
    iBondFrozen = np.zeros([L,L])
    jBondFrozen = np.zeros([L,L])
    for i in np.arange(L):
        for j in np.arange(L):
            if (Ising[i][j] == Ising[next(i)][j]) and (np.random.rand() < freezProb):
                iBondFrozen[i][j] = 1
            if (Ising[i][j] == Ising[i][next(j)]) and (np.random.rand() < freezProb):
                jBondFrozen[i][j] = 1
    return iBondFrozen, jBondFrozen

# H-K algorithm to identify clusters
def properlabel(prp_label,i):
    while prp_label[i] != i:
        i = prp_label[i]
    return i

# Swendsen-Wang cluster
def clusterfind(iBondFrozen,jBondFrozen):
    cluster = np.zeros([L, L])
    prp_label = np.zeros(L**2)
    label = 0
    for i in np.arange(L):
        for j in np.arange(L):
            bonds = 0
            ibonds = np.zeros(4)
            jbonds = np.zeros(4)

            # check to (i-1,j)
            if (i > 0) and iBondFrozen[i-1][j]:
                ibonds[bonds] = i-1
                jbonds[bonds] = j
                bonds += 1
            # (i,j) at i edge, check to (i+1,j)
            if (i == L-1) and iBondFrozen[i][j]:
                ibonds[bonds] = 0
                jbonds[bonds] = j
                bonds += 1
            # check to (i,j-1)
            if (j > 0) and jBondFrozen[i][j-1]:
                ibonds[bonds] = i
                jbonds[bonds] = j-1
                bonds += 1
            # (i,j) at j edge, check to (i,j+1)
            if (j == L-1) and jBondFrozen[i][j]:
                ibonds[bonds] = i
                jbonds[bonds] = 0
                bonds += 1

            # check and label clusters
            if bonds == 0:
                cluster[i][j] = label
                prp_label[label] = label
                label += 1
            else:
                minlabel = label
                for b in np.arange(bonds):
                    plabel = properlabel(prp_label,cluster[ibonds[b]][jbonds[b]])
                    if minlabel > plabel:
                        minlabel = plabel

                cluster[i][j] = minlabel
                # link to the previous labels
                for b in np.arange(bonds):
                    plabel_n = cluster[ibonds[b]][jbonds[b]]
                    prp_label[plabel_n] = minlabel
                    # re-set the labels on connected sites
                    cluster[ibonds[b]][jbonds[b]] = minlabel
    return cluster, prp_label

# flip the cluster spins
def flipCluster(Ising,cluster,prp_label):
    for i in np.arange(L):
        for j in np.arange(L):
            # relabel all the cluster labels with the right ones
            cluster[i][j] = properlabel(prp_label,cluster[i][j])
    sNewChosen = np.zeros(L**2)
    sNew = np.zeros(L**2)
    flips = 0 # get the number of flipped spins to calculate the Endiff and Magdiff
    for i in np.arange(L):
        for j in np.arange(L):
            label = cluster[i][j]
            randn = np.random.rand()
            # mark the flipped label, use this label to flip all the cluster elements with this label
            if (not sNewChosen[label]) and randn < 0.5:
                sNew[label] = +1
                sNewChosen[label] = True
            elif (not sNewChosen[label]) and randn >= 0.5:
                sNew[label] = -1
                sNewChosen[label] = True

            if Ising[i][j] != sNew[label]:
                Ising[i][j] = sNew[label]
                flips += 1

    return Ising,flips

# Calculate the energy for the Ising system
def EnMag(Ising):
    energy = 0
    mag = 0
    for i in np.arange(L):
        for j in np.arange(L):
            energy = energy - Ising[i][j]*(Ising[(i-1)%L][j]+Ising[(i+1)%L][j]+Ising[i][(j-1)%L]+Ising[i][(j+1)%L])
            mag = mag + Ising[i][j]*1/(L**2)
    return energy * 0.5, mag

# Swendsen-Wang Algorithm for observables
def SWang(T):
    Ising = Init()
    # thermal steps to get the equilibrium
    for step in np.arange(ESTEP):
        [iBondFrozen,jBondFrozen] = FreezeBonds(Ising,T)
        [SWcluster,prp_label] = clusterfind(iBondFrozen,jBondFrozen)
        [Ising,flips] = flipCluster(Ising,SWcluster,prp_label)
    # finish with thermal equilibrium, and begin to calc observables
    E_sum = 0
    M_sum = 0
    Esq_sum = 0
    Msq_sum = 0
    
    for step in np.arange(STEP):
        [iBondFrozen,jBondFrozen] = FreezeBonds(Ising,T)
        [SWcluster,prp_label] = clusterfind(iBondFrozen,jBondFrozen)
        [Ising,flips] = flipCluster(Ising,SWcluster,prp_label)
        [E,M] = EnMag(Ising)

        E_sum += E
        M_sum += np.abs(M)
        Esq_sum += E ** 2
        Msq_sum += M ** 2

    E_mean = E_sum / STEP / (L ** 2)
    M_mean = M_sum / STEP
    Esq_mean = Esq_sum / STEP / (L ** 4)
    Msq_mean = Msq_sum / STEP

    return Ising, E_mean, M_mean, Esq_mean, Msq_mean

 
M = np.array([])
E = np.array([])
M_sus = np.array([])
SpcH = np.array([])
for T in np.linspace(0.1, 5, 20):
    [Ising, E_mean, M_mean, Esq_mean, Msq_mean] = SWang(T)
    M = np.append(M, np.abs(M_mean))
    E = np.append(E, E_mean)
    M_sus = np.append(M_sus, 1 / T * (Msq_mean - M_mean ** 2))
    SpcH = np.append(SpcH, 1 / T ** 2 * (Esq_mean - E_mean ** 2))

# plot the figures
T = np.linspace(0.1, 5, 20)

plt.figure()
plt.plot(T, E, 'rx-')
plt.xlabel(r'Temperature $(\frac{J}{k_B})$')
plt.ylabel(r'$\langle E \rangle$ per site $(J)$')
plt.savefig("E.pdf", format='pdf', bbox_inches='tight')

plt.figure()
plt.plot(T, SpcH, 'kx-')
plt.xlabel(r'Temperature $(\frac{J}{k_B})$')
plt.ylabel(r'$C_V$ per site $(\frac{J^2}{k_B^2})$')
plt.savefig("Cv.pdf", format='pdf', bbox_inches='tight')

plt.figure()
plt.plot(T, M, 'bx-')
plt.xlabel(r'Temperature $(\frac{J}{k_B})$')
plt.ylabel(r'$\langle|M|\rangle$ per site $(\mu)$')
plt.savefig("M.pdf", format='pdf', bbox_inches='tight')

plt.figure()
plt.plot(T, M_sus, 'gx-')
plt.xlabel(r'Temperature $(\frac{J}{k_B})$')
plt.ylabel(r'$\chi$ $(\frac{\mu}{k_B})$')
plt.savefig("chi.pdf", format='pdf', bbox_inches='tight')

plt.tight_layout()
fig = plt.gcf()
plt.show()

#T = 0.1
#[Ising, E_mean, M_mean, Esq_mean, Msq_mean] = SWang(T)
#[E1,M1] = EnMag(Ising)
#E2 = E1/(L**2)
## plot the network cluster
#plt.figure()
#plt.matshow(Ising,cmap='cool')
#plt.axis('off')
