"""2D intrusion calculations. This module runs independently of the interface."""
from dataclasses import dataclass, asdict
import json
import numpy as np
from scipy.sparse import lil_matrix, eye
from scipy.sparse.linalg import spsolve, factorized

SECONDS_PER_YEAR = 365.25 * 24 * 60 * 60

@dataclass
class Parameters:
    # 1. Define where the process takes place
    Lx: float = 2000.0
    Lz: float = 2000.0
    spacing: float = 20.0
    xc: float = 1000.0
    zc: float = 1000.0
    width: float = 200.0
    height: float = 400.0
    # 2. Material properties and Tm: Fu et al. (2010), Table 2.
    # Geometry, Tb, head, and duration: my idealized project scenario.
    Tm: float = 1000.0
    Tb: float = 100.0
    rho_intrusion: float = 2700.0
    cp_intrusion: float = 1046.0
    lambda_intrusion: float = 3.0
    rho_rock: float = 2300.0
    cp_rock: float = 1000.0
    lambda_host: float = 2.5
    porosity: float = 0.01
    k_host: float = 1.e-15
    rho_water: float = 1000.0
    cp_water: float = 4180.0
    viscosity_water: float = 2.82e-4
    gravity: float = 9.8
    # 3. Background flow from left to right
    head_left: float = 20.0
    head_right: float = 0.0
    years: float = 5000.0

    @property
    def C_host(self):
        return ((1-self.porosity)*self.rho_rock*self.cp_rock
                + self.porosity*self.rho_water*self.cp_water)


def harmonic_mean(a, b):
    result = np.zeros(np.broadcast_shapes(np.shape(a), np.shape(b)))
    np.divide(2*a*b, a+b, out=result, where=(a+b)>0)
    return result


def make_grid(p):
    # Grid points are at cell centers. Domain boundaries are at cell faces.
    vals = list(asdict(p).values())
    if not all(np.isfinite(v) for v in vals):
        raise ValueError('All parameters must be finite numbers.')
    if min(p.Lx,p.Lz,p.spacing,p.width,p.height,p.years,p.C_host,
           p.lambda_host,p.lambda_intrusion,p.viscosity_water) <= 0:
        raise ValueError('Dimensions, duration, and thermal properties must be positive.')
    if not 0 <= p.porosity < 1 or p.k_host < 0 or p.Tm < p.Tb:
        raise ValueError('Check porosity, permeability, and initial temperature.')
    nx, nz = round(p.Lx/p.spacing), round(p.Lz/p.spacing)
    if min(nx,nz)<4 or max(nx,nz)>240:
        raise ValueError('Use between 4 and 240 cells in each direction.')
    if not np.allclose([nx*p.spacing,nz*p.spacing],[p.Lx,p.Lz]):
        raise ValueError('Domain dimensions must be divisible by the grid spacing.')
    # Align the intrusion with cell faces so its area stays the same.
    edges = [p.xc-p.width/2, p.xc+p.width/2,
             p.zc-p.height/2, p.zc+p.height/2]
    if not (0<edges[0]<edges[1]<p.Lx and 0<edges[2]<edges[3]<p.Lz):
        raise ValueError('The intrusion must lie inside the domain.')
    if not np.allclose(np.array(edges)/p.spacing,
                       np.round(np.array(edges)/p.spacing)):
        raise ValueError('Intrusion boundaries must align with grid cell faces.')
    x = (np.arange(nx)+0.5)*p.spacing
    z = (np.arange(nz)+0.5)*p.spacing
    X,Z = np.meshgrid(x,z)
    intrusion = ((abs(X-p.xc)<p.width/2)&(abs(Z-p.zc)<p.height/2))
    return x,z,X,Z,intrusion


def conduction_operator(C, lam, dx, dz, Tb):
    """Centered differences / intercell fluxes: dT/dt = L T + b.

    Use harmonic means at material interfaces. The Dirichlet boundary Tb
    is half a cell away from the outermost cell centers.
    The application AND the verification notebook use this function.
    """
    nz,nx = C.shape
    ids = np.arange(nx*nz).reshape(nz,nx)
    L = lil_matrix((nx*nz,nx*nz))
    b = np.zeros(nx*nz)
    lx = harmonic_mean(lam[:,:-1],lam[:,1:])
    lz = harmonic_mean(lam[:-1,:],lam[1:,:])
    for j in range(nz):
        for i in range(nx):
            row = ids[j,i]
            for jj,ii,d in [(j,i-1,dx),(j,i+1,dx),(j-1,i,dz),(j+1,i,dz)]:
                if 0<=jj<nz and 0<=ii<nx:
                    lf = lx[j,min(i,ii)] if jj==j else lz[min(j,jj),i]
                    a = lf/(C[j,i]*d*d)
                    L[row,ids[jj,ii]] += a
                else:
                    a = 2*lam[j,i]/(C[j,i]*d*d)
                    b[row] += a*Tb
                L[row,row] -= a
    return L.tocsr(),b


def prepare_conduction(L,b,dt):
    # Crank–Nicolson: average the old-time and new-time contributions.
    I = eye(L.shape[0],format='csr')
    solve = factorized((I-0.5*dt*L).tocsc())
    B = (I+0.5*dt*L).tocsr()
    def step(T_old):
        return solve(B@T_old.ravel()+dt*b).reshape(T_old.shape)
    return step


def solve_flow(p, intrusion):
    # Do not solve head inside the impermeable intrusion.
    nz,nx = intrusion.shape
    K = np.where(intrusion,0.,p.k_host*p.rho_water*p.gravity/p.viscosity_water)
    Kx = harmonic_mean(K[:,:-1],K[:,1:])
    Kz = harmonic_mean(K[:-1,:],K[1:,:])
    qx = np.zeros((nz,nx+1)); qz = np.zeros((nz+1,nx))
    head = np.full((nz,nx),np.nan)
    if p.k_host == 0:
        return head,qx,qz
    active = ~intrusion
    ids = np.full((nz,nx),-1,int)
    ids[active] = np.arange(active.sum())
    A = lil_matrix((active.sum(),active.sum())); b = np.zeros(active.sum())
    d = p.spacing
    for j,i in zip(*np.where(active)):
        row = ids[j,i]
        for jj,ii in [(j,i-1),(j,i+1),(j-1,i),(j+1,i)]:
            if 0<=jj<nz and 0<=ii<nx:
                kf = Kx[j,min(i,ii)] if jj==j else Kz[min(j,jj),i]
                a = kf/d**2
                if a>0:
                    A[row,row] += a
                    A[row,ids[jj,ii]] -= a
            elif ii<0 or ii>=nx:
                # Left/right head is set at domain faces, a distance d/2 away.
                a = 2*K[j,i]/d**2
                A[row,row] += a
                b[row] += a*(p.head_left if ii<0 else p.head_right)
            # Top/bottom boundaries: no water flux.
    head[active] = spsolve(A.tocsr(),b)
    h = np.nan_to_num(head)
    qx[:,1:-1] = -Kx*(h[:,1:]-h[:,:-1])/d
    qz[1:-1,:] = -Kz*(h[1:,:]-h[:-1,:])/d
    qx[:,0] = -K[:,0]*(h[:,0]-p.head_left)/(d/2)
    qx[:,-1] = -K[:,-1]*(p.head_right-h[:,-1])/(d/2)
    return head,qx,qz


def advection_step(T,dt,C,qx,qz,dx,dz,Tb,rho_cp):
    # Water carries the temperature from the upstream side (upwind).
    pad_x = np.pad(T,((0,0),(1,1)),constant_values=Tb)
    pad_z = np.pad(T,((1,1),(0,0)),constant_values=Tb)
    Fx = rho_cp*qx*np.where(qx>=0,pad_x[:,:-1],pad_x[:,1:])
    Fz = rho_cp*qz*np.where(qz>=0,pad_z[:-1,:],pad_z[1:,:])
    divergence = (Fx[:,1:]-Fx[:,:-1])/dx + (Fz[1:,:]-Fz[:-1,:])/dz
    return T-dt*divergence/C


def run_pair(p=None,dt_scale=1.0,progress=None):
    p = p or Parameters()
    if not 0<dt_scale<=1:
        raise ValueError('dt_scale must be greater than 0 and no larger than 1.')
    x,z,X,Z,intrusion = make_grid(p)
    C = np.where(intrusion,p.rho_intrusion*p.cp_intrusion,p.C_host)
    lam = np.where(intrusion,p.lambda_intrusion,p.lambda_host)
    head,qx,qz = solve_flow(p,intrusion)
    L,b = conduction_operator(C,lam,p.spacing,p.spacing,p.Tb)
    rate_conduction = np.max(-L.diagonal())
    outflow = ((np.maximum(qx[:,1:],0)+np.maximum(-qx[:,:-1],0))/p.spacing
               +(np.maximum(qz[1:,:],0)+np.maximum(-qz[:-1,:],0))/p.spacing)
    rho_cp = p.rho_water*p.cp_water
    rate_advection = np.max(rho_cp*outflow/C)
    dt = min(0.5/rate_conduction,
             0.5/rate_advection if rate_advection>0 else np.inf)*dt_scale
    count = int(np.ceil(p.years*SECONDS_PER_YEAR/dt))
    if count>100000:
        raise ValueError('Too many time steps. Reduce the duration or permeability.')
    dt = p.years*SECONDS_PER_YEAR/count
    step_conduction = prepare_conduction(L,b,dt)
    T_initial = np.where(intrusion,p.Tm,p.Tb)
    T_flow = T_initial.copy(); T_no_flow = T_initial.copy()
    # The geometric center lies between four cells: average those cells.
    near = (np.isclose(abs(X-p.xc),abs(x-p.xc).min()) &
            np.isclose(abs(Z-p.zc),abs(z-p.zc).min()))
    times=[0.]; center_flow=[float(T_flow[near].mean())]
    center_no_flow=center_flow.copy()
    mean_flow=[float(T_flow[intrusion].mean())]; mean_no_flow=mean_flow.copy()
    save_steps=set(np.linspace(0,count,41).round().astype(int))
    snapshot_times=[0.]; snapshots=[T_flow.copy()]; snapshots_no=[T_no_flow.copy()]
    for step in range(1,count+1):
        T_star = step_conduction(T_flow)
        T_flow = advection_step(T_star,dt,C,qx,qz,p.spacing,p.spacing,p.Tb,rho_cp)
        T_no_flow = step_conduction(T_no_flow)
        year=step*dt/SECONDS_PER_YEAR
        times.append(year)
        center_flow.append(float(T_flow[near].mean()))
        center_no_flow.append(float(T_no_flow[near].mean()))
        mean_flow.append(float(T_flow[intrusion].mean()))
        mean_no_flow.append(float(T_no_flow[intrusion].mean()))
        if step in save_steps:
            snapshot_times.append(year); snapshots.append(T_flow.copy()); snapshots_no.append(T_no_flow.copy())
        if progress and (step%max(1,count//20)==0 or step==count):
            progress(step/count)
    divergence_q = (qx[:,1:]-qx[:,:-1])/p.spacing+(qz[1:,:]-qz[:-1,:])/p.spacing
    return dict(parameters=asdict(p),x=x,z=z,intrusion=intrusion,head=head,qx=qx,qz=qz,
                times=np.array(times),center_flow=np.array(center_flow),
                center_no_flow=np.array(center_no_flow),mean_flow=np.array(mean_flow),
                mean_no_flow=np.array(mean_no_flow),snapshot_times=np.array(snapshot_times),
                snapshots=np.array(snapshots),snapshots_no=np.array(snapshots_no),
                dt_years=dt/SECONDS_PER_YEAR,n_steps=count,
                effective_area=float(intrusion.sum()*p.spacing**2),
                max_flow_divergence=float(abs(divergence_q).max()),
                max_final_map_difference=float(abs(T_no_flow-T_flow).max()))


def browser_run(parameter_json):
    r=run_pair(Parameters(**json.loads(parameter_json)))
    def plain(v):
        if isinstance(v,np.ndarray): return v.tolist()
        if isinstance(v,np.generic): return v.item()
        return v
    return json.dumps({k:plain(v) for k,v in r.items()},allow_nan=True).replace('NaN','null')
