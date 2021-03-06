import numpy as np
from utils import I


class OFUL:
    def __init__(self, d, K, L, sigma, alpha, l, Sw, Sx, C, delta=0.01):
        self.alpha = alpha
        self.l = l
        self.C = C
        self.sigma = sigma
        self.sigma_pert = None
        self.Sx = Sx
        self.Sw = Sw
        self.K = K
        self.L = L
        self.d = d
        self.delta = delta
        self.t = 0

        self.ld = self.l * I(d)
        self.xxt = [np.zeros((d, d)) for _ in range(K)]
        self.Y = [np.zeros(d) for _ in range(K)]

    def step(self, x, M, b):
        self.t += 1
        y = np.zeros(self.K)

        if np.prod(M.shape) == 0:
            M = np.zeros((self.K, self.d, self.d))
            b = np.zeros((self.K, self.d))

        ucb_bonus = np.zeros(self.K)
        for a in range(self.K):
            if np.sum(self.Y[a]) == 0:
                return a
            Ma_inv = np.linalg.pinv(M[a])
            Pa = I(self.d) - Ma_inv @ M[a]
            Ma_ba = Ma_inv @ b[a]
            PVP_inv = np.linalg.pinv(Pa @ (self.ld + self.xxt[a]) @ Pa)
            Pw = PVP_inv @ (self.Y[a] - self.xxt[a] @ Ma_ba)
            y[a] = x @ Pw + x @ Ma_ba
            ucb_bonus[a] = self.beta * np.sqrt(x @ PVP_inv @ x)

        a = np.argmax(y + self.alpha * ucb_bonus)
        return a

    @property
    def beta(self):
        return (self.sigma + self.Sx * self.Sw * self.C) * \
               np.sqrt((self.d - self.L) * np.log((self.K / self.delta)*(1 + self.t / self.l))) + np.sqrt(self.l) * self.Sw

    def update(self, x, a, r):
        self.xxt[a] += x[:, np.newaxis] @ x[:, np.newaxis].T
        self.Y[a] += r * x






