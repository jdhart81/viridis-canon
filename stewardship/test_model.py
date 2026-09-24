import unittest
from math import exp,expm1,sqrt
import numpy as np
from scipy.integrate import quad
from model import (Parameters,stock,segment,finite_ode,schedule,tail_bound,
                   mutual_information,fresh_channel,score_unique_targets,symbolic_checks,
                   validate_state)

class CertificateTests(unittest.TestCase):
    def test_seven_symbolic_identities(self):
        checks=symbolic_checks(); self.assertEqual(len(checks),7); self.assertTrue(all(checks.values()))

    def test_normalized_witness(self):
        o=Parameters().optimum()
        for k,v in dict(stock=.6,attempt_rate=.12,duty=.2,information_rate=.072,value=.72).items():
            self.assertAlmostEqual(o[k],v,places=13)

    def test_nonunit_normalization_and_degradation(self):
        p=Parameters(K=7,phi=3,omega=.4); o=p.optimum()
        self.assertAlmostEqual(o['stock'],4.2)
        self.assertAlmostEqual(p.g(o['stock']),p.phi*o['attempt_rate'])
        self.assertAlmostEqual(o['duty'],p.g(o['stock'])/(p.phi*p.omega*o['stock']))
        out=schedule(p,o['stock'],[(2,.8),(3,.05)],.7)
        self.assertLess(abs(out['identity_residual']),2e-10)

    def test_capacity_is_not_sustained_output(self):
        p=Parameters(); o=p.optimum()
        self.assertGreater(p.omega*o['stock'],o['attempt_rate'])
        self.assertLess(p.g(o['stock'])-p.phi*p.omega*o['stock'],0)

    def test_cap_equality_is_feasible(self):
        o=Parameters(omega=.2).optimum(); self.assertAlmostEqual(o['duty'],1.)

    def test_insufficient_cap_rejected(self):
        with self.assertRaises(ValueError): Parameters(omega=.199).optimum()
        with self.assertRaises(ValueError): Parameters(omega=np.nextafter(.2,0.)).optimum()

    def test_discount_scope(self):
        for r in (1.,1.1):
            with self.assertRaises(ValueError): Parameters(r=r).optimum()
        for r in (0.,-.1,float('nan'),float('inf')):
            with self.assertRaises(ValueError): Parameters(r=r)

    def test_parameter_rejections(self):
        for kwargs in ({'K':0},{'alpha':-1},{'phi':-1},{'omega':0},{'m':-.5},{'m':1.5}):
            with self.assertRaises(ValueError): Parameters(**kwargs)

    def test_bounds_and_overshoot_detection(self):
        p=Parameters()
        for d in (-1e-8,1+1e-8,float('nan')):
            with self.assertRaises(ValueError): validate_state(p,d)
        for h in (-.1,.7):
            with self.assertRaises(ValueError): validate_state(p,.6,h)
        for u in (-.01,1.01):
            with self.assertRaises(ValueError): stock(p,.6,u,1)

    def test_ode_state_bounds(self):
        p=Parameters()
        for d in (0.,1e-4,.6,1.):
            for u in (0.,.2,1.):
                end,_=finite_ode(p,d,u,20)
                self.assertGreaterEqual(end,-2e-10); self.assertLessEqual(end,1+2e-10)
                self.assertAlmostEqual(end,stock(p,d,u,20),places=9)

    def test_critical_logistic_drift(self):
        p=Parameters(); self.assertAlmostEqual(stock(p,.6,.5,4),.6/(1+.5*.6*4))
        d,_=finite_ode(p,.6,.5,4); self.assertAlmostEqual(d,stock(p,.6,.5,4),places=10)

    def test_forcing_lifetime_not_zero(self):
        value=segment(Parameters(),.6,1,np.inf)[0]
        self.assertAlmostEqual(value,.2407207380857683,places=12)
        self.assertGreater(value,.2)

    def test_initial_forcing_output_and_short_horizon(self):
        p=Parameters(); o=p.optimum()
        self.assertAlmostEqual(p.q(.6)*p.omega*.6/o['information_rate'],5.)
        self.assertGreater(segment(p,.6,1,.2)[0],o['value']*(-expm1(-p.r*.2)))

    def test_finite_horizon_terminal_term(self):
        p=Parameters(); T=.3; d=stock(p,.6,1,T)
        potential=quad(lambda t:exp(-p.r*t)*p.F(stock(p,.6,1,t)),0,T)[0]
        with_terminal=(p.W(.6)-exp(-p.r*T)*p.W(d)+potential)/p.phi
        direct=segment(p,.6,1,T)[0]
        self.assertAlmostEqual(direct,with_terminal,places=12)
        self.assertGreater(abs(direct-(p.W(.6)+potential)/p.phi),.05)

    def test_arbitrary_initial_stock_bound(self):
        p=Parameters()
        for d in (.05,.4,.8,1.):
            out=schedule(p,d,[(2,.4)],.8)
            self.assertLessEqual(out['value'],p.upper_bound(d)+1e-10)
            self.assertLess(abs(out['identity_residual']),2e-10)
        self.assertNotAlmostEqual(p.upper_bound(.8),p.optimum()['value'])

    def test_stationary_equality(self):
        p=Parameters(); o=p.optimum(); out=schedule(p,o['stock'],[],o['duty'])
        self.assertAlmostEqual(out['value'],o['value'],places=12)
        self.assertAlmostEqual(out['regret_integral'],0,places=12)

    def test_raw_certificate(self):
        p=Parameters(K=2,m=0); o=p.optimum()
        self.assertAlmostEqual(o['stock'],.8); self.assertAlmostEqual(o['attempt_rate'],.24)
        self.assertAlmostEqual(o['value'],2.4)
        out=schedule(p,.8,[],1)
        self.assertAlmostEqual(out['value'],1.1382360418576283,places=11)
        square=quad(lambda t:exp(-p.r*t)*(stock(p,.8,1,t)-.8)**2,0,np.inf)[0]*p.alpha/(p.phi*p.K)
        self.assertAlmostEqual(o['value']-out['value'],square,places=10)

    def test_raw_feasibility(self):
        self.assertAlmostEqual(Parameters(m=0,omega=.3).optimum()['duty'],1.)
        with self.assertRaises(ValueError): Parameters(m=0,omega=.29).optimum()

    def test_zero_damage_ablation(self):
        p=Parameters(phi=0)
        with self.assertRaises(ValueError): p.optimum()
        for t in (0,1,20): self.assertAlmostEqual(stock(p,.6,1,t),stock(p,.6,.2,t))
        self.assertAlmostEqual(segment(p,.6,1,np.inf)[0]/segment(p,.6,.2,np.inf)[0],5.)

    def test_independent_objective_and_tail(self):
        p=Parameters(); T=300
        _,ode=finite_ode(p,.6,1,T); direct=segment(p,.6,1,np.inf)[0]
        self.assertLess(abs(ode-direct),1e-10+tail_bound(p,T))
        self.assertLess(tail_bound(p,T),1e-12)

    def test_channel_by_joint_enumeration(self):
        for q in (0,.1,.3,.6,.9,1): self.assertAlmostEqual(mutual_information(q),q,places=14)

    def test_random_known_stock_conditioning(self):
        # Conditional MI is the stock-weighted expectation, not a random scalar.
        stocks=[.1,.8]; probs=[.25,.75]
        self.assertAlmostEqual(sum(w*mutual_information(d) for d,w in zip(stocks,probs)),.625)

    def test_fresh_targets_no_double_count(self):
        self.assertEqual(score_unique_targets([(0,1),(1,None),(2,0)]),2)
        with self.assertRaises(ValueError): score_unique_targets([(0,1),(0,1)])

    def test_seeded_channel_and_confidence_reporting(self):
        for i,q in enumerate((.1,.3,.6,.9)):
            report=fresh_channel(q,100000,1000+i)
            self.assertLess(abs(report['mean_gain_bits']-q),6*sqrt(q*(1-q)/100000))
            self.assertEqual(report['unique_target_count'],100000)
            self.assertEqual(report['interval_covers_stipulated_q'],report['wilson_95'][0]<=q<=report['wilson_95'][1])

    def test_general_exponents_and_matched_schedules(self):
        rng=np.random.default_rng(21444226)
        for m in (0,1,2):
            p=Parameters(K=3,phi=2,m=m); o=p.optimum()
            self.assertAlmostEqual(o['stock'],p.K*((m+1)*p.alpha-p.r)/((m+2)*p.alpha))
            for _ in range(5):
                out=schedule(p,o['stock'],list(zip(rng.uniform(.1,2,4),rng.uniform(0,1,4))),float(rng.uniform()))
                self.assertGreaterEqual(out['regret_integral'],-2e-10)
                self.assertLess(abs(out['identity_residual']),2e-10)

if __name__=='__main__': unittest.main(verbosity=2)
