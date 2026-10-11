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


class MeanMeas():
    def __init__(
        self, 
        n_dims:int,
        res:float,
        dims_min:np.ndarray,
        dims_max:np.ndarray,
        cons_init_value:float=0.0,
    ):
        
        # Maps
        self.map_c = Map( # gas concentration
            n_dims=n_dims,
            n_features=1,
            res=res,
            dims_min=dims_min,
            dims_max=dims_max,
            init_vals=cons_init_value,
        )
        self.map_n = Map( # number of measurements
            n_dims=n_dims,
            n_features=1,
            res=res,
            dims_min=dims_min,
            dims_max=dims_max,
            init_vals=0.0,
        )

        self.first_update = False

    def update(
        self,
        poss:np.ndarray,
        cons:np.ndarray,
    ):
        """
        Update the map with the provided data. 
        Assumes chronological order of measurements.
        Args:
            poss (np.ndarray): Measurement positions (n_meas, n_dims).
            cons (np.ndarray): Gas concentration values (n_meas,).
        """
        if self.first_update:
            self.update_first_batch(
                poss=poss,
                cons=cons,
            )
            self.first_update = False
            return
        
        for i in range(poss.shape[0]):
            self.update_step(
                pos=poss[i],
                con=cons[i],
            )

    def update_step(
        self,
        pos:np.ndarray,
        con:np.ndarray,
    ):
        """
        Update the map with the provided data.
        Args:
            pos (np.ndarray): Measurement position, (n_dims,).
            con (np.ndarray): Gas concentration value, (1,).
        """
        n_prev = self.map_n.get_cell_vals(
            poss=pos.reshape(1, -1),
            copy_array=False,
        ).flatten()
        con_prev = self.map_c.get_cell_vals(
            poss=pos.reshape(1, -1),
            copy_array=False,
        ).flatten()

        n_new = n_prev + 1
        con_new = (con_prev*n_prev + con) / n_new

        self.map_n.set_cell_vals(
            poss=pos.reshape(1, -1),
            vals=n_new,
            copy_array=False,
        )
        self.map_c.set_cell_vals(
            poss=pos.reshape(1, -1),
            vals=con_new,
            copy_array=False,
        )

    def update_first_batch(
        self,
        poss:np.ndarray,
        cons:np.ndarray,
    ):
        """
        Update the map with the provided data. 
        Assumes chronological order of measurements.
        Args:
            poss (np.ndarray): Measurement positions (n_meas, n_dims).
            cons (np.ndarray): Gas concentration values (n_meas,).
        """
        idxs = self.map_c.pos2flat(
            poss=poss,
        )

        # Count the number of measurements in each cell
        c_ = np.bincount(idxs)
        counts = np.zeros(self.map_c.num_cells)
        counts[:c_.shape[0]] = c_

        # Add up the concentration values in each cell and calculate the mean
        grid = np.zeros(self.map_c.num_cells)
        np.add.at(grid, idxs, cons)
        grid /= counts

        self.map_n.set_cell_vals(
            idxs_flat=np.arange(self.map_c.num_cells),
            vals=counts,
            copy_array=False,
        )
        self.map_c.set_cell_vals(
            idxs_flat=np.arange(self.map_c.num_cells),
            vals=grid,
            copy_array=False,
        )

    def con2val(
        self,
        cons:np.ndarray,
        copy_array:bool=True,
    ):
        """
        Convert gas concentrations to filter values. For the mean measurement filter
        the filter values are equal to gas concentrations
        Args:
            cons (np.ndarray): Gas concentration values (n_meas,).
            copy_array (bool): Copy the input array.
        Returns:
            np.ndarray: Filter values (n_meas,).
        """
        if copy_array:
            return cons.copy()
        return cons
    
    def val2con(
        self,
        vals:np.ndarray,
        copy_array:bool=True,
    ):
        """
        Convert filter values to gas concentration values. For the mean measurement filter
        the filter values are equal to gas concentrations
        Args:
            vals (np.ndarray): Filter values (n_meas,).
            copy_array (bool): Copy the input array.
        Returns:
            np.ndarray: Gas concentration values (n_meas,).
        """
        if copy_array:
            return vals.copy()
        return vals