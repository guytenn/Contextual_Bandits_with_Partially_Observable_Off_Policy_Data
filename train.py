import numpy as np
from OFUL import OFUL
from time import time
from data import MbSampler, DataManager


class Trainer:
    def __init__(self, env, w, **kwargs):
        self.args = kwargs

        self.env = env
        self.d = self.args['d']
        self.K = self.args['K']
        if not self.args['perturbations']:
            self.M = np.random.rand(self.K, self.d, self.d) / np.sqrt(self.d)
        else:
            self.M = None
        self.w = w
        self.Sw = np.max(np.linalg.norm(w, axis=1))
        self.Sx = env.x_norm
        self.sigma = env.sigma
        self.mu = self.K

    def execute(self, T, L, alpha_l_factor, data_manager: DataManager = None):
        start = time()
        print(f'Started Job: (T={T}, L={L}, alpha_l={alpha_l_factor})')

        args = self.args

        if not args['perturbations']:
            M = self.M[:, 0:L, :]
            b = np.zeros((self.K, L))
            N = 0
            for a in range(self.K):
                b[a] = M[a] @ self.w[a]
            sampler = None
        else:
            sampler = MbSampler(data_manager, L, self.d, self.K, args['calc_r12'])
            b = np.array(sampler.b)
            M = None
            N = data_manager.N
            elapsed_time = time() - start
            print(f'It took {elapsed_time}s to build dataset')
            start = time()


        regret = 0
        regret_vec = []

        if args['perturbations'] and not args['calc_r12']:
            C = self.Sw * self.Sx * sampler.C
        else:
            C = 0
        Algo = OFUL(self.d, self.K, L, self.sigma, alpha_l_factor, args['l'], self.Sw, self.Sx, C, args['delta'])

        last_time = start
        for t in range(T):
            if self.args['verbose']:
                elapsed_time = time() - last_time
                if elapsed_time > 60:
                    last_time = time()
                    print(f'Mid-run: (t/T={t}/{T}, L={L}, alpha={alpha_l_factor}, N={N}, regret={regret}, time={time() - start}s, time_per_100_iter={100 * (time()-start) / t}s)')
            x = self.env.sample_x()
            if self.args['perturbations']:
                M, _ = sampler.step(x)
            a = Algo.step(x, M, b)
            real_r, r = self.env.sample_r(x, a)
            Algo.update(x, a, r)
            regret += self.env.best_r(x) - real_r
            regret_vec.append(regret)
        elapsed_time = time()-start
        print(f'Done: (T={T}, L={L}, alpha_l={alpha_l_factor}, regret={regret}, N={N}, time={elapsed_time}s, time_per_100_iter={100 * elapsed_time / T}s)')

        return regret_vec