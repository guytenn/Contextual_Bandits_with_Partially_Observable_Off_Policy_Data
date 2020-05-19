import numpy as np
from utils import softmax

class Mu:
    def __init__(self):
        self.tot_sum = 0
        self.t = 0

    def step(self, x):
        self.t += 1
        self.tot_sum += x
        return self.value

    @property
    def value(self):
        return self.tot_sum / self.t


class Sigma:
    def __init__(self):
        self.tot_sum = 0
        self.t = 0

    def step(self, x, y, mu_x, mu_y):
        self.t += 1
        self.tot_sum += (x[:, np.newaxis] - mu_x[:, np.newaxis]) @ \
                        (y[:, np.newaxis] - mu_y[:, np.newaxis]).T
        return self.value

    @property
    def value(self):
        return self.tot_sum / max((self.t - 1), 1)


class R:
    def __init__(self):
        self.mu_x = Mu()
        self.mu_y = Mu()
        self.sigma = Sigma()
        self.t = 0

    def step(self, x, y=None):
        if y is None:
            y = np.copy(x)
        _mu_x = self.mu_x.step(x)
        _mu_y = self.mu_y.step(y)
        self.sigma.step(x, y, _mu_x, _mu_y)
        self.t = self.sigma.t
        return self.value

    @property
    def value(self):
        return self.sigma.value + self.mu_x.value[:, np.newaxis] @ self.mu_y.value[:, np.newaxis].T


class DataManager:
    def __init__(self, env, d, K, N=100000):
        self.env = env
        self.N = N
        self.K = K
        self.d = d
        self.Phi = np.random.randn(K, d)
        self.X, self.A, self.r, self.Pa = self._create_dataset(N)

    def reset(self):
        self.X, self.A, self.r, self.Pa = self._create_dataset(self.N)

    def pib(self, x):
        p = softmax(self.Phi @ x)
        return int(np.random.choice(self.K, p=p))

    def _create_dataset(self, N):
        X = np.zeros((N, self.d))
        A = np.zeros(N, dtype=int)
        r = np.zeros(N)
        for i in range(N):
            X[i] = self.env.sample_x()
            A[i] = self.pib(X[i])
            _, r[i] = self.env.sample_r(X[i], A[i])
        Pa = A / N
        return X, A, r, Pa


class MbSampler:
    def __init__(self, data_manager: DataManager, L, d, K):
        self.data_manager = data_manager

        self.L = L
        self.d = d
        self.K = K
        N = data_manager.N

        # For calculating b (R11 is also used for M)
        R11_vec = [R() for _ in range(K)]
        Y = [Mu() for _ in range(self.K)]
        for i in range(N):
            R11_vec[data_manager.A[i]].step(data_manager.X[i, :L])
            Y[data_manager.A[i]].step(data_manager.X[i, :L] * data_manager.r[i])
        self.R11_inv_vec = [np.linalg.inv(R11.value) for R11 in R11_vec]
        self.b = [self.R11_inv_vec[i] @ Y[i].value for i in range(K)]

        # For calculating M
        # self.R11_inv_vec = [np.pad(R11_inv, [(0, d - L), (0, d - L)]) for R11_inv in R11_inv_vec]
        self.R12 = [R() for _ in range(K)]
        self.M = [[] for _ in range(K)]

        # self.￿D = np.pad(np.eye(L), [(0, d-L), (0 , d-L)])

    def step(self, x):
        if self.L == 0:
            return np.array([]), self.b

        a = self.data_manager.pib(x)
        self.R12[a].step(x[:self.L], x[self.L:])
        for i in range(self.K):
            if self.R12[i].t == 0:
                B = np.zeros((self.L, self.d - self.L))
            else:
                B = self.R11_inv_vec[i] @ self.R12[i].value
                # R12 = np.pad(self.R12[i].value, [(0, self.L), (self.d - self.L, 0)])
                # B = self.R11_inv_vec[i] @ R12
            self.M[i] = np.concatenate([np.eye(self.L), B]).T
            # self.M[i] = self.D + B
        return self.M, self.b


if __name__ == '__main__':
    from env import LinearContextualBandit

    L = 2
    d = 4
    K = 2
    N = 10000

    w = np.random.rand(K, d)

    env = LinearContextualBandit(w)

    sampler = MbSampler(env, L, d, K, N)

    for _ in range(N):
        M, b = sampler.step(env.sample_x())

    for _ in range(K):
        print(M[0] @ w[0] - np.concatenate([b[0], np.zeros(d-L)]))
