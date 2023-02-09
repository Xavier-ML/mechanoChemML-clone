import numpy as np

import tensorflow as tf

import mechanoChemML.src.pde_layers as pde_layers
from mechanoChemML.workflows.pde_solver.pde_workflow_steady_state_heter import PDEWorkflowSteadyState

class LayerDiffusionSteadyStateBulkResidual(pde_layers.LayerBulkResidual):
    """
    Steady state bulk residual
    """
    # data: [batch, in_height, in_width, in_channels]
    # filter: [filter_height, filter_width, in_channels, out_channels]
    # dh is needed.

    def __init__(self, dh, normalization_factor=2.0, D0=1.0, name='R_bulk_diffusion'):
        super(LayerDiffusionSteadyStateBulkResidual, self).__init__(name=name)

        self.dh = dh
        self.dof = 1
        self.normalization_factor = normalization_factor
        self.D0 = D0
        self.dim = 2

        self.initialize_arrays()

    def call(self, input):
        """ 
        apply the int (B^T H) dV for element wise c value with 4 nodal value
        - input data: [batch, in_height, in_width, 4] (2x2 nodal values for u)
        - output: [batch, in_height, in_width, 4] (nodal value residual)
        """

        data = self.GetElementInfo(input)
        data = data * self.normalization_factor - 0.5 * self.normalization_factor

        shape=data.get_shape()[0:].as_list()    
        domain_shape = shape[1:3]

        # expand D0 to be an image representation
        self.D0 = tf.expand_dims(self.D0, axis=2)
        self.D0 = tf.expand_dims(self.D0, axis=3)
        self.D0 = tf.tile(self.D0, [1,domain_shape[0],domain_shape[0],1])
        self.D0 = tf.reshape(self.D0, [-1, 1])

        # print('domain_shape: ', domain_shape)
        gradu1, gradu2, gradu3, gradu4 = self.ComputeGraduAtGPs(data)
        H1, H2, H3, H4 = self.ConstitutiveRelation(gradu1, gradu2, gradu3, gradu4)
        R = self.ComputeIntTranBxP(H1, H2, H3, H4, domain_shape)
        # print(type(self.D0), type(R))
        return R

    def ConstitutiveRelation(self, gradu1, gradu2, gradu3, gradu4):
        # ----------- testing stochastic D0 -------------------
        # random_D0 = tf.random.uniform(tf.shape(gradu1), minval=self.D0-0.5, maxval=self.D0+0.5, dtype=tf.float32)
        # random_D0 = tf.random.normal(tf.shape(gradu1), self.D0, self.D0*0.4, tf.float32, seed=1024)
        # H1 = tf.multiply(gradu1, random_D0) 
        #-----------------------------------------------------

        H1 = self.D0 * gradu1
        H2 = self.D0 * gradu2
        H3 = self.D0 * gradu3
        H4 = self.D0 * gradu4
        # # print('D0: ', tf.shape(self.D0), 'gradu1: ', tf.shape(gradu1))
        # # H1 = tf.reshape(H1, [-1, self.dim*self.dof])
        # # H2 = tf.reshape(H2, [-1, self.dim*self.dof])
        # # H3 = tf.reshape(H3, [-1, self.dim*self.dof])
        # # H4 = tf.reshape(H4, [-1, self.dim*self.dof])
        # # # print('D0: ', tf.shape(self.D0), 'gradu1: ', tf.shape(gradu1))
        return H1, H2, H3, H4


class WeakPDESteadyStateDiffusion(PDEWorkflowSteadyState):
    """

    """

    def __init__(self):
        super().__init__()
        self.dof = 1
        self.dof_name = ['c']
        self.problem_name = 'diffusion'
        self.D0 = 1.0
        self.UseTwoNeumannChannel = True

    def _bulk_residual(self, y_pred, pde_parameters):
        """
        bulk residual for steady state diffusion
        """
        elem_bulk_residual=LayerDiffusionSteadyStateBulkResidual(dh=self.dh, D0=pde_parameters)(y_pred)
        return elem_bulk_residual


if __name__ == '__main__':
    """ Weak PDE constrained NN for steady-state diffusion """
    problem = WeakPDESteadyStateDiffusion()
    problem.run()
    # problem.test(test_folder='DNS')
    # problem.test(test_folder='Test_inter')
    # problem.test(test_folder='Test_extra')
    # problem.debug_problem(use_label=False)
    # problem.debug_problem(use_label=True)
    # problem.test_residual_gaussian(noise_std=1e-4, sample_num=1000)
