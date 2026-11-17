"""Checks using the same solver functions as the application."""
import numpy as np
from simulation import (Parameters, make_grid, conduction_operator,
                        prepare_conduction, solve_flow, advection_step, SECONDS_PER_YEAR)


def sine_test(spacing=20.,dt_years=5.,years=1000.):
    # Test case only: homogeneous rock, with no intrusion and no flow.
    length=2000.; n=round(length/spacing)
    x=(np.arange(n)+.5)*spacing
    X,Z=np.meshgrid(x,x)
    p=Parameters(); C=np.full((n,n),p.C_host); lam=np.full((n,n),p.lambda_host)
    L,b=conduction_operator(C,lam,spacing,spacing,p.Tb)
    shape=np.sin(np.pi*X/length)*np.sin(np.pi*Z/length)
    initial=p.Tb+100*shape
    count=int(np.ceil(years/dt_years)); dt=years*SECONDS_PER_YEAR/count
    step=prepare_conduction(L,b,dt)
    numerical=initial.copy()
    for _ in range(count): numerical=step(numerical)
    alpha=p.lambda_host/p.C_host
    exact=p.Tb+100*shape*np.exp(-alpha*np.pi**2*(2/length**2)*years*SECONDS_PER_YEAR)
    # Exact semidiscrete solution: separate time error from spatial error.
    rate=alpha*8/spacing**2*np.sin(np.pi*spacing/(2*length))**2
    discrete_exact=p.Tb+100*shape*np.exp(-rate*years*SECONDS_PER_YEAR)
    error=numerical-exact
    return dict(x=x,numerical=numerical,exact=exact,error=error,
                max_error=float(abs(error).max()),rmse=float(np.sqrt(np.mean(error**2))),
                time_error=float(abs(numerical-discrete_exact).max()))


def basic_checks():
    p=Parameters(spacing=20.)
    x,z,X,Z,intrusion=make_grid(p)
    assert np.isclose(intrusion.sum()*p.spacing**2,p.width*p.height)
    C=np.where(intrusion,p.rho_intrusion*p.cp_intrusion,p.C_host)
    lam=np.where(intrusion,p.lambda_intrusion,p.lambda_host)
    head,qx,qz=solve_flow(p,intrusion)
    L,b=conduction_operator(C,lam,p.spacing,p.spacing,p.Tb)
    dt=SECONDS_PER_YEAR
    uniform=np.full(C.shape,p.Tb)
    after=advection_step(prepare_conduction(L,b,dt)(uniform),dt,C,qx,qz,
                         p.spacing,p.spacing,p.Tb,p.rho_water*p.cp_water)
    err=float(abs(after-p.Tb).max())
    assert err<1e-8
    div=(qx[:,1:]-qx[:,:-1])/p.spacing+(qz[1:,:]-qz[:-1,:])/p.spacing
    relative=float(abs(div).max()/(abs(qx).max()/p.spacing))
    assert relative<1e-8
    qin=float(qx[:,0].sum()*p.spacing); qout=float(qx[:,-1].sum()*p.spacing)
    assert np.isclose(qin,qout,rtol=1e-8,atol=0)
    # Check that water cannot cross the intrusion boundary.
    assert np.max(abs(qx[:,1:-1][intrusion[:,:-1]|intrusion[:,1:]]))==0
    assert np.max(abs(qz[1:-1,:][intrusion[:-1,:]|intrusion[1:,:]]))==0
    return dict(area=float(intrusion.sum()*p.spacing**2),uniform_error=err,
                flow_relative_residual=relative,inflow=qin,outflow=qout)

if __name__=='__main__':
    print(basic_checks())
    errors=[sine_test(h)['max_error'] for h in [40.,20.,10.]]
    print('Errors for 40, 20, and 10 m grids:',errors)
    assert errors[0]/errors[1]>3.8 and errors[1]/errors[2]>3.8
    print('Checks completed.')
