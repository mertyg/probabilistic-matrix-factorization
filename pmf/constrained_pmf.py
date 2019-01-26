import numpy as np
import matplotlib.pyplot as plt

# Probabilistic Matrix Factorization with Adaptive Priors


class CPMF:
    def __init__(self, params):
        self.params = params
        self.n_users = params["users"]+1
        self.lamda = params["lambda"]
        self.n_products = params["products"]+1
        self.mean_rat = 0
        self.K = 0
        self.train_res = []
        self.test_res = []

    def transform_ratings(self, ratings, mode="inverse"):
        if mode == "inverse":
            return ratings*(self.K-1)+1
        else:
            return (ratings-1)/(self.K-1)

    def sigmoid(self, x):
        return 1/(1+np.exp(-x))

    def fit(self, train_data, test_data):
        epochs = self.params["epoch"]
        lr = self.params["lr"]
        lamda = self.params["lambda"]
        n_features = self.params["features"]
        batch_size = self.params["batch_size"]
        momentum = self.params["momentum"]
        w_users = 0.1*np.random.randn(self.n_users, n_features)
        w_products = 0.1*np.random.randn(self.n_products, n_features)
        self.K = np.max([np.max(train_data[:, 2]), np.max(test_data[:, 2])])
        train_data[:, 2] = self.transform_ratings(train_data[:, 2], mode="pre-process")
        test_data[:, 2] = self.transform_ratings(test_data[:, 2], mode="pre-process")
        self.mean_rat = np.mean(train_data[:, 2])
        update_u = np.zeros((self.n_users, n_features))
        update_p = np.zeros((self.n_products, n_features))

        print("starting")
        for epoch in range(epochs):
            print("Epoch: ", epoch, end=" ")
            np.random.shuffle(train_data)

            for batch in range(round(train_data.shape[0]/batch_size)):
                train_batch = train_data[batch*batch_size:(batch+1)*batch_size]
                users = train_batch[:, 0].astype(np.int)
                products = train_batch[:, 1].astype(np.int)
                ratings = train_batch[:, 2] # - self.mean_rat
                pred = np.sum(np.multiply(w_users[users, :], w_products[products, :]), 1)
                g_pred = self.sigmoid(pred)
                l1_error = g_pred-ratings
                sigmoid_grad = np.multiply(g_pred[:,np.newaxis], (1-g_pred)[:,np.newaxis])
                pred_grad_u = np.multiply(l1_error[:, np.newaxis],w_products[products])
                pred_grad_p = np.multiply(l1_error[:, np.newaxis], w_users[users])
                batch_grad_u = 2*np.multiply(sigmoid_grad,pred_grad_u)+lamda*w_users[users]
                batch_grad_p = 2*np.multiply(sigmoid_grad,pred_grad_p) + lamda*w_products[products]
                dw_u = np.zeros((self.n_users, n_features))
                dw_p = np.zeros((self.n_products, n_features))

                for r in range(batch_size):
                    dw_u[users[r]] += batch_grad_u[r]
                    dw_p[products[r]] += batch_grad_p[r]
                update_u = momentum*update_u + lr*dw_u/batch_size
                update_p = momentum*update_p + lr*dw_p/batch_size
                w_users -= update_u
                w_products -= update_p

            u_idx = train_data[:, 0].astype(np.int)
            p_idx = train_data[:, 1].astype(np.int)
            training_loss = self.compute_rmse_loss(w_users[u_idx], w_products[p_idx], train_data[:, 2])
            print("finished. Current training RMSE: ", training_loss, end=" ")
            self.train_res.append(training_loss)
            u_idx = test_data[:, 0].astype(np.int)
            p_idx = test_data[:, 1].astype(np.int)
            test_loss = self.compute_rmse_loss(w_users[u_idx], w_products[p_idx], test_data[:, 2])
            print("Current validation RMSE: ", test_loss)
            self.test_res.append(test_loss)

    def compute_obj_loss(self, w_u, w_p, rat):
        w_u = w_u
        w_p = w_p
        pred = np.sum(np.multiply(w_u, w_p), 1)
        g_pred = self.sigmoid(pred) # + self.mean_rat
        error = np.linalg.norm(g_pred - rat)**2 + \
                0.5 * self.lamda*(np.linalg.norm(w_u)**2 + np.linalg.norm(w_p)**2)
        return error/rat.shape[0]

    def compute_rmse_loss(self, w_u, w_p, rat):
        pred = np.sum(np.multiply(w_u, w_p), 1)
        g_pred = self.sigmoid(pred)
        #g_pred = g_pred+self.mean_rat
        g_pred = self.transform_ratings(g_pred)
        rat = self.transform_ratings(rat)
        err = rat - g_pred
        loss = np.linalg.norm(err)/np.sqrt(pred.shape[0])
        return loss

    def plot_loss(self):
        plt.plot(np.arange(self.params["epoch"]), self.train_res, color="red", label="Training Loss")
        plt.plot(np.arange(self.params["epoch"]), self.test_res, color="blue", label="Test Loss")
        plt.legend()
        plt.grid()
        plt.title("RMSE Loss vs Epoch for Vanilla PMF")
        plt.xlabel("Epoch")
        plt.ylabel("Loss")
        plt.show()


