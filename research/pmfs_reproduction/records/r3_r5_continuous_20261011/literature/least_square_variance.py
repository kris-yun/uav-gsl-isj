# MIT License
#
# Copyright (c) 2025 Nicolaj Bösel-Schmid
# Contact: nicolaj.schmid@epfl.ch
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import sys
import os
import numpy as np

if os.getcwd() not in sys.path:
    sys.path.append(os.getcwd())
from mapping.map import Map
from helper.math.schur_complement import SchurComplement

class LeastSquareVariance():
    def __init__(
        self,
        map_w:Map,
        kernel_precision:float=30,
        print_info:bool=False,
    ):

        # Parameters
        self.kernel_precision = kernel_precision
        self.print_info = print_info

        # Maps
        self.map_w = map_w

        self.map_params = Map(
            n_dims=map_w.n_dims,
            n_features=map_w.n_dims + 1,
            res=map_w.res,
            dims_min=map_w.min,
            dims_max=map_w.max,
            init_vals=0.0,
        )

        # Regularization parameters
        self.gamma_cons = 1e-4
        self.gamma_grad = 1e-4
        self.gamma_wind = 1e-4

        self.sigma_omega = None
        self.sc = SchurComplement()
        
    def __call__(
        self,
        poss_meas:np.ndarray,
        cons_meas:np.ndarray,
    ):
        poss_meas = poss_meas.copy() # (n_meas, n_dims)
        cons_meas = cons_meas.copy() # (n_meas,)

        if self.print_info:
            print(f"ls_var.__call__: Construct sub matrices.")

        poss_cells = self.map_w.get_cell_poss(
            idxs_flat=np.arange(self.map_w.num_cells),
        ) # (n_cells, n_dims) 

        alpha = self.kernel_norm(
            poss_targets=poss_meas,
            poss_sources=poss_cells,
        ) # (n_meas, n_cells)


        X = self._construct_X(
            poss_cells=poss_cells,
            poss_meas=poss_meas,
        ) # (n_meas, n_weights, n_cells)
        AX = X * alpha[:, None, :] # (n_meas, n_weights, n_cells)

        XTA2X = self._mul(
            mat1 = AX.transpose(1, 0, 2), # (n_weights, n_meas, n_cells)
            mat2 = AX, # (n_meas, n_weights, n_cells)
        ) # (n_weights, n_weights, n_cells)

        # Regularization
        XTA2X_R = self._regularize(
            XTA2X=XTA2X,
        )

        if self.print_info:
            print(f"ls_var.__call__: Solve linear system.")

        XTA2X_R_inv = self.sc.inverse(
            M = XTA2X_R,
        ) # (n_weights, n_weights, n_cells)


        XTA2 = (AX *alpha[:, None, :]).transpose(1, 0, 2) # (n_weights, n_meas, n_cells)
        XTA2X_R_inv_XTA2 = self._mul(
            mat1 = XTA2X_R_inv, # (n_weights, n_weights, n_cells)
            mat2 = XTA2, # (n_weights, n_meas, n_cells)
        ) # (n_weights, n_meas, n_cells)

        omega = np.einsum("ijk, j -> ik", XTA2X_R_inv_XTA2, cons_meas) # (n_weights, n_cells)
        self.map_params.set_cell_vals(
            vals=omega.T, # (n_cells, n_weights)
            poss=poss_cells,
        )

        if self.print_info:
            print(f"ls_var.__call__: Calculate variance of weights.")

        beta = self.kernel_norm(
            poss_targets=poss_cells,
            poss_sources=poss_meas,
        ) # (n_cells, n_meas)
        beta = beta.T # (n_meas, n_cells)

        y_pred = np.sum(X * omega[None, :, :], axis=1) # (n_meas, n_cells) # TODO: merge two lines
        y_pred = np.sum(beta * y_pred, axis=1) # (n_meas,)

        stdy = ((cons_meas - y_pred)**2)[None, :, None] # (1, n_meas, 1)
        XTA2X_R_inv_XTA2_stdy = XTA2X_R_inv_XTA2 * stdy # (n_weights, n_meas, n_cells)
        self.sigma_omega = self._mul(
            mat1 = XTA2X_R_inv_XTA2_stdy, # (n_weights, n_meas, n_cells)
            mat2 = XTA2X_R_inv_XTA2_stdy.transpose(1, 0, 2), # (n_meas, n_weights, n_cells)
        ) # (n_weights, n_weights, n_cells)

        if self.print_info:
            print(f"ls_var.__call__: Done.")

    def predict(
        self,
        poss_meas:np.ndarray,
    ):
        """
        Predict concentration values.
        Args:
            poss_meas (np.ndarray): Prediction positions (n_meas, n_dims).
        Returns:
            y_pred (np.ndarray): Predicted concentration values (n_meas,).
            y_pred_var (np.ndarray): Predicted concentration variance (n_meas,).
        """
        if self.print_info:
            print(f"ls_var.predict: Construct sub matrices.")

        poss_meas = poss_meas.copy() # (n_meas, n_dims)
        poss_cells = self.map_w.get_cell_poss(
            idxs_flat=np.arange(self.map_w.num_cells),
        ) # (n_cells, n_dims)

        beta = self.kernel_norm(
            poss_targets=poss_cells,
            poss_sources=poss_meas,
        ) # (n_cells, n_meas)
        beta = beta.T # (n_meas, n_cells)
        assert np.sum(beta, axis=1).all() == 1.0, \
                "Sum of beta is not 1.0."

        X = self._construct_X(
            poss_cells=poss_cells,
            poss_meas=poss_meas,
        ) # (n_meas, n_weights, n_cells)

        # Mean prediction
        if self.print_info:
            print(f"ls_var.predict: Predict mean.")

        omega = self.map_params.get_cell_vals(
            poss=poss_cells,
        ) # (n_cells, n_weights)
        omega = omega.T[None, :, :] # (1, n_weights, n_cells)
        
        y_pred = np.sum(X * omega, axis=1) # (n_meas, n_cells) # TODO: merge two lines
        y_pred = np.sum(beta * y_pred, axis=1) # (n_meas,)


        # Variance prediction
        if self.print_info:
            print(f"ls_var.predict: Predict variance.")

        X_sigma = self._mul(
            mat1=X, # (n_meas, n_weights, n_cells)
            mat2=self.sigma_omega, # (n_weights, n_weights, n_cells)
        ) # (n_meas, n_weights, n_cells)

        X_sigma_XT = np.einsum("ijk, ijk -> ik", X_sigma, X) # (n_meas, n_cells)

        y_pred_var = np.sum(beta**2 * X_sigma_XT, axis=1) # (n_meas,)

        if self.print_info:
            print(f"ls_var.predict: Done.")
        
        return y_pred, y_pred_var


    def kernel_norm(
        self,
        poss_targets:np.ndarray,
        poss_sources:np.ndarray,
    ):
        """
        Norm kernel.
        Args:
            poss_targets (np.ndarray): Target positions (n_target, n_dims).
            poss_sources (np.ndarray): Source positions (n_source, n_dims).
        Returns:
            (np.ndarray): Kernel matrix (n_target, n_source).
        """
        poss_targets = poss_targets.copy()
        poss_sources = poss_sources.copy()

        # reshape and tile
        poss_sources = poss_sources.reshape(1, poss_sources.shape[0], poss_sources.shape[1]) # (1, n_source, n_dims)
        poss_sources = np.tile(poss_sources, (poss_targets.shape[0], 1, 1)) # (n_target, n_source, n_dims)
        poss_targets = poss_targets.reshape(poss_targets.shape[0], 1, poss_targets.shape[1]) # (n_target, 1, n_dims)
        poss_targets = np.tile(poss_targets, (1, poss_sources.shape[1], 1)) # (n_target, n_source, n_dims)

        a = np.exp(- self.kernel_precision * np.sum(np.abs(poss_targets - poss_sources), axis=2)) # (n_target, n_source)
        a = a / np.sum(a, axis=0) # (n_target, n_source)
        return a
    
    def wind_norm(
        self,
        poss_targets:np.ndarray,
        poss_sources:np.ndarray,
        wind:np.ndarray,
    ):
        """
        Norm kernel.
        Args:
            poss_targets (np.ndarray): Target positions (n_target, n_dims).
            poss_sources (np.ndarray): Source positions (n_source, n_dims).
            wind (np.ndarray): Wind vectors (n_source, n_dims).
        Returns:
            U (np.ndarray): Gradient matrix 1 (n_target, n_source).
            V (np.ndarray): Gradient matrix 2 (n_target, n_source).
            W (np.ndarray): Wind matrix (n_target, n_source).
        """
        poss_targets = poss_targets.copy()
        poss_sources = poss_sources.copy()
        wind = wind.copy()
        
        # reshape and tile
        poss_sources = poss_sources.reshape(1, poss_sources.shape[0], poss_sources.shape[1]) # (1, n_source, n_dims)
        poss_targets = poss_targets.reshape(poss_targets.shape[0], 1, poss_targets.shape[1]) # (n_target, 1, n_dims)
        wind = wind.reshape(1, wind.shape[0], wind.shape[1]) # (1, n_source, n_dims)
        poss_sources = np.tile(poss_sources, (poss_targets.shape[0], 1, 1)) # (n_target, n_source, n_dims)
        poss_targets = np.tile(poss_targets, (1, poss_sources.shape[1], 1)) # (n_target, n_source, n_dims)
        wind = np.tile(wind, (poss_targets.shape[0], 1, 1)) # (n_target, n_source, n_dims)
        poss_delta = poss_targets - poss_sources # (n_target, n_source, n_dims)

        # Compute the gradient matrices U and V
        wind_norm = np.linalg.norm(wind, axis=2) # (n_target, n_source)
        if poss_targets.shape[2] == 3:
            U = np.cross(wind/wind_norm[:,:,None], np.array([[[0, 0, 1]]])) # (n_target, n_source, n_dims)
            V = np.cross(wind/wind_norm[:,:,None], U) # (n_target, n_source, n_dims)
            U = np.sum((U * poss_delta), axis=2) # (n_target, n_source)
            V = np.sum((V * poss_delta), axis=2) # (n_target, n_source)
        elif poss_targets.shape[2] == 2:
            U = np.concatenate([(wind[:,:,1]/wind_norm)[:,:,None], -(wind[:,:,0]/wind_norm)[:,:,None]], axis=2) # (n_target, n_source, n_dims)
            U = np.sum((U * poss_delta), axis=2)
            V = None

        # Compute wind matrix W
        W = np.sum((wind * poss_delta), axis=2) / (np.linalg.norm(wind, axis=2)**2) # (n_target, n_source)

        # # TODO: implement case where wind is parallel to z-axis and were wind is zero
        # U_zero = (np.linalg.norm(U, axis=2) < 1e-3) # case where wind is parallel to z-axis
        # U[U_zero] = np.cross(wind[U_zero], np.array([[[0, 1, 0]]]))

        return U, V, W

    def matrix_dist(
        self,
        poss_targets:np.ndarray,
        poss_sources:np.ndarray,
    ):
        """
        Distance matrix.
        Args:
            poss_targets (np.ndarray): Target positions (n_target, n_dims).
            poss_sources (np.ndarray): Source positions (n_source, n_dims).
        Returns:
            (np.ndarray): Distance matrix (n_target, n_source, n_dims).
        """
        poss_targets = poss_targets.copy()
        poss_sources = poss_sources.copy()

        # reshape and tile
        poss_targets = poss_targets.reshape(poss_targets.shape[0], 1, poss_targets.shape[1]) # (n_target, 1, n_dims)
        poss_sources = poss_sources.reshape(1, poss_sources.shape[0], poss_sources.shape[1]) # (1, n_source, n_dims)
        poss_targets = np.tile(poss_targets, (1, poss_sources.shape[1], 1)) # (n_target, n_source, n_dims)
        poss_sources = np.tile(poss_sources, (poss_targets.shape[0], 1, 1)) # (n_target, n_source, n_dims)

        return poss_targets - poss_sources # (n_target, n_source, n_dims)
    

    def _construct_X(
        self,
        poss_cells:np.ndarray,
        poss_meas:np.ndarray,
    ):
        """
        Construct feature matrix X.
        Args:
            poss_cells (np.ndarray): Cell positions (n_cells, n_dims).
            poss_meas (np.ndarray): Measurement positions (n_meas, n_dims).
        Returns:
            X (np.ndarray): Feature matrix X (n_meas, n_weights, n_cells).
        """
        wind = self.map_w.get_cell_vals(
            poss=poss_cells,
        ) # (n_cells, n_dims)

        U, V, W = self.wind_norm(
            poss_targets=poss_meas,
            poss_sources=poss_cells,
            wind=wind,
        ) # (n_meas, n_cells), (n_meas, n_cells), (n_meas, n_cells)

        if self.map_w.n_dims == 2:
            return np.concatenate([
                np.ones_like(U)[:, None, :], # (n_meas, 1, n_cells)
                U[:, None, :], # (n_meas, 1, n_cells)
                W[:, None, :], # (n_meas, 1, n_cells)
            ], axis=1) # (n_meas, n_weights, n_cells)
        elif self.map_w.n_dims == 3:
            return np.concatenate([
                np.ones_like(U)[:, None, :], # (n_meas, 1, n_cells)
                U[:, None, :], # (n_meas, 1, n_cells)
                V[:, None, :], # (n_meas, 1, n_cells)
                W[:, None, :], # (n_meas, 1, n_cells)
            ], axis=1) # (n_meas, n_weights, n_cells)
        else:
            raise ValueError(f"Unknown dimension: {self.map_w.n_dims}.")
        
    def _regularize(
        self,
        XTA2X:np.ndarray,
    ):
        """
        Regularize matrix XTA2X.
        Args:
            XTA2X (np.ndarray): Matrix XTA2X (n_weights, n_weights, n_cells).
        Returns:
            (np.ndarray): Regularized matrix XTA2X (n_weights, n_weights, n_cells).
        """
        C = self.map_w.num_cells
        XTA2X[0, 0] += self.gamma_cons * np.ones((C))
        XTA2X[1, 1] += self.gamma_grad * np.ones((C))
        if self.map_w.n_dims == 3:
            XTA2X[2, 2] += self.gamma_grad * np.ones((C))
        XTA2X[-1, -1] += self.gamma_wind * np.ones((C))
        return XTA2X
    
    def _mul(
        self,
        mat1:np.ndarray,
        mat2:np.ndarray,
    ):
        """
        Multiply two MxM block matrices.
        Args:
            mat1 (np.ndarray): Matrix 1 (N, L, K).
            mat2 (np.ndarray): Matrix 2 (L, M, K).
        Returns:
            (np.ndarray): Result (N, L, K).
        """
        return np.einsum("ilk, ljk -> ijk", mat1, mat2)


    
   