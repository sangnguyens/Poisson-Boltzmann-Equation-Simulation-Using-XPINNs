import tensorflow as tf
import numpy as np


class PDE_utils():

    DTYPE = 'float32'
    pi = tf.constant(np.pi, dtype=DTYPE)

    def __init__(self):

        self.maintain_precond = False
            
    
    def get_loss(self, X_batches, model):
        L = dict()
        L['R'] = 0.0
        L['D'] = 0.0
        L['N'] = 0.0
        L['K'] = 0.0
        L['I'] = 0.0
        L['P'] = 0.0

        #residual
        if 'R' in self.mesh.meshes_names: 
            X,SU = X_batches['R']
            loss_r = self.residual_loss(self.mesh,model,self.mesh.get_X(X),SU)
            L['R'] += loss_r    

        #dirichlet 
        if 'D' in self.mesh.meshes_names:
            X,U = X_batches['D']
            loss_d = self.dirichlet_loss(self.mesh,model,X,U)
            L['D'] += loss_d

        #neumann
        if 'N' in self.mesh.meshes_names:
            X,U = X_batches['K']
            loss_n = self.neumann_loss(self.mesh,model,X,U)
            L['N'] += loss_n

        # data known
        if 'K' in self.mesh.meshes_names:
            X,U = X_batches['K']
            loss_k = self.data_known_loss(self.mesh,model,X,U)
            L['K'] += loss_k    

        return L


    # Dirichlet
    def dirichlet_loss(self,mesh,model,XD,UD):
        Loss_d = 0
        u_pred = model(XD)
        loss = tf.reduce_mean(tf.square(UD - u_pred)) 
        Loss_d += loss
        return Loss_d


    def neumann_loss(self,mesh,model,XN,UN,V=None):
        Loss_n = 0
        X = mesh.get_X(XN)
        grad = self.directional_gradient(mesh,model,X,self.normal_vector(X))
        loss = tf.reduce_mean(tf.square(UN-grad))
        Loss_n += loss
        return Loss_n
    
        # Dirichlet
    def data_known_loss(self,mesh,model,XK,UK):
        Loss_d = 0
        u_pred = model(XK)
        loss = tf.reduce_mean(tf.square(UK - u_pred)) 
        Loss_d += loss
        return Loss_d



    ####################################################################################################################################################

    # Define boundary condition
    def fun_u_b(self,x, y, z, value):
        n = x.shape[0]
        return tf.ones((n,1), dtype=self.DTYPE)*value

    def fun_ux_b(self,x, y, z, value):
        n = x.shape[0]
        return tf.ones((n,1), dtype=self.DTYPE)*value


    ####################################################################################################################################################

    # Differential operators

    def laplacian(self,mesh,model,X):
        x,y,z = X
        with tf.GradientTape(persistent=True) as tape:
            tape.watch(x)
            tape.watch(y)
            tape.watch(z)
            R = mesh.stack_X(x,y,z)
            u = model(R)
            u_x = tape.gradient(u,x)
            u_y = tape.gradient(u,y)
            u_z = tape.gradient(u,z)
        u_xx = tape.gradient(u_x,x)
        u_yy = tape.gradient(u_y,y)
        u_zz = tape.gradient(u_z,z)
        del tape

        return u_xx + u_yy + u_zz

    def gradient(self,mesh,model,X):
        x,y,z = X
        with tf.GradientTape(persistent=True,watch_accessed_variables=False) as tape:
            tape.watch(x)
            tape.watch(y)
            tape.watch(z)
            R = mesh.stack_X(x,y,z)
            u = model(R)
        u_x = tape.gradient(u,x)
        u_y = tape.gradient(u,y)
        u_z = tape.gradient(u,z)
        del tape

        return (u_x,u_y,u_z)
    
    def directional_gradient(self,mesh,model,X,n_v):
        gradient = self.gradient(mesh,model,X)
        dir_deriv = 0
        for j in range(3):
            dir_deriv += n_v[j]*gradient[j]

        return dir_deriv