"""Independent deterministic fluid benchmark. Not the missing supplied package.

Units: D,K=stock; H=attempt/time; phi=stock/attempt; alpha,r=1/time;
omega=attempt/(stock*time); q=bit/attempt; J=discounted predictive bits.
Numerical quadrature error estimates are not rigorous interval bounds.
"""
from dataclasses import dataclass, asdict
from fractions import Fraction
from math import exp, expm1, isfinite, log, log2, sqrt
import numpy as np
from scipy.integrate import quad, solve_ivp
from scipy.optimize import brentq

@dataclass(frozen=True)
class Parameters:
    alpha: float = .5
    K: float = 1.
    phi: float = 1.
    omega: float = 1.
    r: float = .1
    m: int = 1

    def __post_init__(self):
        if not all(isfinite(x) and x > 0 for x in (self.alpha,self.K,self.omega,self.r)):
            raise ValueError('alpha,K,omega,r must be finite and positive; r=0 is separate')
        if not isfinite(self.phi) or self.phi < 0:
            raise ValueError('phi must be finite and nonnegative')
        if type(self.m) is not int or self.m < 0:
            raise ValueError('m must be a nonnegative integer')

    def g(self, d): return self.alpha*d*(1-d/self.K)
    def q(self, d): return (d/self.K)**self.m
    def W(self, d): return d**(self.m+1)/((self.m+1)*self.K**self.m)
    def F(self, d): return self.q(d)*self.g(d)-self.r*self.W(d)

    def optimum(self):
        if self.phi == 0 or self.r >= (self.m+1)*self.alpha:
            raise ValueError('outside positive-phi interior theorem')
        d = self.K*((self.m+1)*self.alpha-self.r)/((self.m+2)*self.alpha)
        u = (self.alpha+self.r)/((self.m+2)*self.phi*self.omega)
        # Interpret declared decimal parameters exactly for the feasibility gate.
        # Floating evaluation alone can round a just-infeasible ratio down to 1.
        if (Fraction(str(self.alpha))+Fraction(str(self.r)) >
                (self.m+2)*Fraction(str(self.phi))*Fraction(str(self.omega))):
            raise ValueError('holding candidate is infeasible')
        h = self.g(d)/self.phi
        return {'stock':d,'attempt_rate':h,'duty':u,'information_rate':self.q(d)*h,
                'value':self.q(d)*h/self.r}

    def upper_bound(self, d0):
        validate_state(self,d0)
        s = self.optimum()['stock']
        return (self.W(d0)+self.F(s)/self.r)/self.phi


def validate_state(p,d,h=None,tolerance=0.):
    if not isfinite(d) or d < -tolerance or d > p.K+tolerance:
        raise ValueError('stock out of bounds; no clipping permitted')
    if h is not None and (not isfinite(h) or h < -tolerance or h > p.omega*d+tolerance):
        raise ValueError('inadmissible control')


def stock(p,d0,u,t):
    """Exact constant-duty logistic trajectory, including alpha=phi*omega*u."""
    validate_state(p,d0)
    if not isfinite(u) or not 0 <= u <= 1 or not isfinite(t) or t < 0:
        raise ValueError('invalid duty/time')
    if d0 == 0: return 0.
    a = p.alpha-p.phi*p.omega*u
    b = p.alpha/p.K
    if a == 0: return d0/(1+b*d0*t)
    # Stable in both exponential directions.
    if a > 0: return d0/(exp(-a*t)+b*d0*(-expm1(-a*t))/a)
    return d0*exp(a*t)/(1+b*d0*expm1(a*t)/a)


def segment(p,d0,u,duration,offset=0.):
    """Direct objective integral; does not use W, F, or a regret certificate."""
    return quad(lambda t: exp(-p.r*(offset+t))*p.q(stock(p,d0,u,t))*
                u*p.omega*stock(p,d0,u,t), 0, duration, epsabs=2e-12, epsrel=2e-12)


def finite_ode(p,d0,u,T):
    """Independent DOP853 dynamics and objective as a second ODE state."""
    validate_state(p,d0)
    if not 0<=u<=1 or not isfinite(T) or T<0: raise ValueError('invalid control/horizon')
    def rhs(t,y):
        d=y[0]; h=u*p.omega*d
        return [p.g(d)-p.phi*h, exp(-p.r*t)*p.q(d)*h]
    sol=solve_ivp(rhs,(0,T),[d0,0.],method='DOP853',rtol=2e-11,atol=1e-13,
                  dense_output=True,max_step=.5)
    if not sol.success: raise RuntimeError(sol.message)
    # Detection tolerates solver roundoff, never repairs/clips a bad solution.
    for d in sol.sol(np.linspace(0,T,1001))[0]: validate_state(p,d,u*p.omega*d,2e-10)
    return float(sol.y[0,-1]),float(sol.y[1,-1])


def schedule(p,d0,stages,tail_duty):
    """All finite stages plus independently integrated infinite constant-duty tail."""
    validate_state(p,d0)
    t=0.; d=d0; value=0.; error=0.; potential=0.; gap=0.
    s=p.optimum()['stock']
    for duration,u in [*stages,(np.inf,tail_duty)]:
        if duration<=0: raise ValueError('duration must be positive')
        # Validate even when a quadrature routine samples no endpoints.
        stock(p,d,u,0.)
        v,e=segment(p,d,u,duration,t); value+=v; error+=e
        pot,_=quad(lambda x: exp(-p.r*(t+x))*p.F(stock(p,d,u,x)),0,duration,
                   epsabs=2e-11,epsrel=2e-11)
        reg,_=quad(lambda x: exp(-p.r*(t+x))*(p.F(s)-p.F(stock(p,d,u,x)))/p.phi,
                   0,duration,epsabs=2e-11,epsrel=2e-11)
        potential+=pot; gap+=reg
        if isfinite(duration): d=stock(p,d,u,duration); t+=duration
    bound=p.upper_bound(d0)
    return {'value':value,'regret_integral':gap,'arbitrary_initial_upper_bound':bound,
            'identity_residual':bound-value-gap,'quadrature_error_estimate':error,
            'accounting_residual':value-(p.W(d0)+potential)/p.phi}


def tail_bound(p,T):
    """Analytic bound on omitted objective, using 0<=q<=1,H<=omega*K.
    Evaluation in float is not outward-rounded interval arithmetic.
    """
    if not isfinite(T) or T<0: raise ValueError('invalid truncation')
    return p.omega*p.K*exp(-p.r*T)/p.r


def mutual_information(q):
    if not 0<=q<=1: raise ValueError('invalid reveal probability')
    joint={(0,0):q/2,(1,1):q/2,(0,'?'):(1-q)/2,(1,'?'):(1-q)/2}
    py={o:sum(v for (x,z),v in joint.items() if z==o) for o in (0,1,'?')}
    return sum(v*log2(v/(.5*py[o])) for (x,o),v in joint.items() if v>0)


def fresh_channel(q,n,seed):
    if not 0<=q<=1 or n<=0: raise ValueError('invalid channel')
    rng=np.random.default_rng(seed)
    targets=rng.integers(0,2,n)  # distinct trial indices, fresh independent targets
    reveal=rng.random(n)<q      # independent of target values
    observations=np.where(reveal,targets,-1)
    # Posterior true-label probability uses only the observed symbol.
    posterior=np.where(observations==-1,.5,1.)
    gain=1+np.log2(posterior)
    mean=float(gain.mean()); z=1.959963984540054
    center=(mean+z*z/(2*n))/(1+z*z/n)
    radius=z*sqrt(mean*(1-mean)/n+z*z/(4*n*n))/(1+z*z/n)
    return {'q':q,'n':n,'seed':seed,'mean_gain_bits':mean,
            'wilson_95':[center-radius,center+radius],
            'interval_covers_stipulated_q':center-radius<=q<=center+radius,
            'unique_target_count':n}


def score_unique_targets(trials):
    seen=set(); total=0.
    for target_id,observation in trials:
        if target_id in seen: raise ValueError('target counted twice')
        if observation not in (0,1,None): raise ValueError('invalid observation')
        seen.add(target_id); total+=float(observation is not None)
    return total


def symbolic_checks():
    import sympy as s
    a,k,r,f,d=s.symbols('a k r f d',positive=True)
    g=lambda x:a*x*(1-x/k)
    ds=k*(2*a-r)/(3*a); dr=k*(a-r)/(2*a)
    W=lambda x:x*x/(2*k); F=lambda x:x*g(x)/k-r*W(x)
    identities={
        'information_cubic_gap':F(ds)-F(d)-a/(2*k*k)*(d-ds)**2*(2*d+ds),
        'raw_square_gap':g(dr)-r*dr-g(d)+r*d-a/k*(d-dr)**2,
        'information_stationarity':s.diff(F(d),d).subs(d,ds),
        'raw_stationarity':s.diff(g(d)-r*d,d).subs(d,dr),
        'held_rate_balance':g(ds)-f*(g(ds)/f),
        'information_held_duty':g(ds)/(f*ds)-(a+r)/(3*f),
        'raw_held_duty':g(dr)/(f*dr)-(a+r)/(2*f)}
    return {n:s.factor(v)==0 for n,v in identities.items()}


def benchmark():
    p=Parameters(); o=p.optimum(); d=o['stock']
    forcing=schedule(p,d,[],1.)
    raw=Parameters(m=0).optimum()['stock']
    transition=brentq(lambda t: stock(p,d,1,t)-raw,0,10,xtol=1e-14)
    raw_u=p.g(raw)/(p.phi*p.omega*raw)
    comparator=schedule(p,d,[(transition,1.)],raw_u)
    crossover=brentq(lambda T:o['value']*(-expm1(-p.r*T))-segment(p,d,1,T)[0],.01,20,xtol=1e-13)
    T=300.; od,oj=finite_ode(p,d,1.,T)
    force_bound=p.omega*d*d/p.K/(p.r+2*(p.phi*p.omega-p.alpha))
    rng=np.random.default_rng(21444226); residuals=[]; regrets=[]
    for m in (0,1,2):
        pm=Parameters(m=m); dm=pm.optimum()['stock']
        for _ in range(128):
            stages=list(zip(rng.uniform(.05,2,12),rng.uniform(0,1,12)))
            out=schedule(pm,dm,stages,float(rng.uniform()))
            residuals.append(abs(out['identity_residual'])); regrets.append(out['regret_integral'])
    nodamage=Parameters(phi=0)
    full=segment(nodamage,d,1,np.inf)[0]; slow=segment(nodamage,d,.2,np.inf)[0]
    return {'evidence_class':'independent numerical/symbolic model check; not supplied-package reproduction, Lean theorem, or empirical validation',
        'parameters':asdict(p),'initial_stock':d,'stationary':o,'forcing':forcing,
        'raw_target':comparator,'raw_transition_time':transition,
        'initial_forcing_rate':p.q(d)*p.omega*d,'ratio':o['value']/forcing['value'],
        'crossover':crossover,'analytic_forcing_upper_bound':force_bound,
        'analytic_ratio_lower_bound':o['value']/force_bound,
        'independent_ode':{'horizon':T,'value':oj,'stock':od,'omitted_tail_analytic_bound_float':tail_bound(p,T),'difference_from_infinite_quadrature':oj-forcing['value']},
        'symbolic_checks':symbolic_checks(),
        'schedules':{'seed':21444226,'per_exponent':128,'exponents':[0,1,2],'total':384,'finite_stages':12,'tail':'infinite constant duty','max_absolute_residual':max(residuals),'minimum_regret':min(regrets)},
        'channel':[fresh_channel(q,100000,1000+i) for i,q in enumerate((.1,.3,.6,.9))],
        'zero_damage':{'full_rate':full,'one_fifth_rate':slow,'ratio':full/slow}}
