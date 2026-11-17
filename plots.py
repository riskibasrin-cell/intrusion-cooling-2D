"""Plot the results. Calculations remain in simulation.py."""
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle


def plot_results(r):
    p=r['parameters']; x=r['x']; z=r['z']
    X,Z=np.meshgrid(x,z)
    def axes_model(ax):
        ax.add_patch(Rectangle((p['xc']-p['width']/2,p['zc']-p['height']/2),
                     p['width'],p['height'],fill=False,edgecolor='cyan'))
        ax.set(xlim=(0,p['Lx']),ylim=(p['Lz'],0),xlabel='x (m)',ylabel='Local z (m)')
        ax.set_aspect('equal')
    fig1,ax=plt.subplots(figsize=(7,6),layout='constrained')
    im=ax.pcolormesh(X,Z,r['head'],shading='nearest',cmap='viridis')
    qx=.5*(r['qx'][:,:-1]+r['qx'][:,1:]); qz=.5*(r['qz'][:-1,:]+r['qz'][1:,:])
    sl=(slice(None,None,5),slice(None,None,5))
    if np.max(abs(qx))+np.max(abs(qz))>0:
        ax.quiver(X[sl],Z[sl],qx[sl],qz[sl],color='white',angles='xy')
    axes_model(ax); ax.set_title('Hydraulic head and groundwater flow direction')
    fig1.colorbar(im,ax=ax,label='Hydraulic head (m)')
    fig2,axes=plt.subplots(2,3,figsize=(12,8),layout='constrained')
    for ax,k in zip(axes.flat,np.linspace(0,len(r['snapshots'])-1,6).round().astype(int)):
        im=ax.pcolormesh(X,Z,r['snapshots'][k],shading='nearest',cmap='hot',vmin=p['Tb'],vmax=p['Tm'])
        axes_model(ax); ax.set_title(f"Time = {r['snapshot_times'][k]:.1f} years")
    fig2.colorbar(im,ax=list(axes.flat),label='Temperature (°C)',shrink=.8)
    fig3,ax=plt.subplots(figsize=(8,5),layout='constrained')
    ax.plot(r['times'],r['center_no_flow'],'k--',label='Center — no flow')
    ax.plot(r['times'],r['center_flow'],color='royalblue',label='Center — with flow')
    ax.axhline(p['Tb'],color='gray',ls=':',label='Background temperature')
    ax.set(xlabel='Time (years)',ylabel='Intrusion center temperature (°C)',title='Intrusion cooling comparison')
    ax.grid(alpha=.3); ax.legend()
    return fig1,fig2,fig3
