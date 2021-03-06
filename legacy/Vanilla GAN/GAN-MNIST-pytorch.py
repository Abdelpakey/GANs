import torch
from torch.nn import init
from torch.autograd import Variable
import torchvision
import matplotlib.pyplot as plt 
import numpy as np 
import os
import time
import imageio


def my_weight_init(m):
    # classname = m.__class__.__name__
    if isinstance(m, torch.nn.Linear):
        # torch.nn.init.xavier_uniform(m.weight.data)
        # torch.nn.init.constant(m.bias.data, 0)
        init.xavier_uniform(m.weight.data)
        init.constant(m.bias.data, 0)

class Generator(torch.nn.Module):
    def __init__(self, input_size, n_hidden=128, n_output=728, alpha=0.2):
        super().__init__()
        self.alpha = alpha
        self.fc1 = torch.nn.Linear(input_size, n_hidden, bias=True)
        self.fc2 = torch.nn.Linear(self.fc1.out_features, n_output, bias=True)

        for m in self.modules():
            my_weight_init(m)
            

    def forward(self, input):
        out = torch.nn.functional.leaky_relu(self.fc1(input), negative_slope=self.alpha)
        out = torch.nn.functional.tanh(self.fc2(out))

        return out

class Discriminator(torch.nn.Module):
    def __init__(self, input_size, n_hidden=128, n_output=1, alpha=0.2):
        super().__init__()
        self.alpha = alpha
        self.fc1 = torch.nn.Linear(input_size, n_hidden, bias=True)
        self.fc2 = torch.nn.Linear(self.fc1.out_features, n_output, bias=True)

        for m in self.modules():
            my_weight_init(m)

    def forward(self, input):
        out = torch.nn.functional.leaky_relu(self.fc1(input), negative_slope=self.alpha)
        out = torch.nn.functional.sigmoid(self.fc2(out))

        return out

# image save function
def save_generator_output(G, fixed_z, img_str, title):
    n_images = fixed_z.size()[0]
    n_rows = np.sqrt(n_images).astype(np.int32)
    n_cols = np.sqrt(n_images).astype(np.int32)
    
    z_ = Variable(fixed_z.cuda())
    samples = G(z_)
    samples = samples.cpu().data.numpy()

    fig, axes = plt.subplots(nrows=n_rows, ncols=n_cols, figsize=(5,5), sharey=True, sharex=True)
    for ax, img in zip(axes.flatten(), samples):
        ax.axis('off')
        ax.set_adjustable('box-forced')
        ax.imshow(img.reshape((28,28)), cmap='Greys_r', aspect='equal')
    plt.subplots_adjust(wspace=0, hspace=0)
    plt.suptitle(title)
    plt.savefig(img_str)
    plt.close(fig)

'''
Build
'''
class GAN:
    def __init__(self, x_size, z_size, learning_rate):

        self.x_size, self.z_size = x_size, z_size

        # build network
        self.G = Generator(z_size, n_output=x_size)
        self.D = Discriminator(x_size, n_output=1)
        self.G.cuda()
        self.D.cuda()

        # optimizer
        beta1 = 0.5
        self.BCE_loss = torch.nn.BCELoss()
        self.G_opt = torch.optim.Adam(self.G.parameters(), lr=learning_rate, betas=[beta1, 0.999])
        self.D_opt = torch.optim.Adam(self.D.parameters(), lr=learning_rate, betas=[beta1, 0.999])

'''
Start training
'''
def train(net, epochs, batch_size, data_loc, print_every=30):
    # data_loader normalize [0, 1] ==> [-1, 1]
    transform = torchvision.transforms.Compose([
        torchvision.transforms.ToTensor(),
        torchvision.transforms.Normalize(mean=(0.5, 0.5, 0.5), std=(0.5, 0.5, 0.5))
    ])
    train_loader = torch.utils.data.DataLoader(
        torchvision.datasets.MNIST(data_loc, train=True, download=True, transform=transform),
        batch_size=batch_size, shuffle=True)

    step = 0
    losses = []
    fixed_z = torch.Tensor(25, net.z_size).uniform_(-1, 1)
    for e in range(epochs):
        for x_, _ in train_loader:
            step += 1
            '''
            Train in Discriminator
            '''
            # reshape input image
            x_ = x_.view(-1, net.x_size)
            current_batch_size = x_.size()[0]

            # create labels for loss computation
            y_real_ = torch.ones(current_batch_size)
            y_fake_ = torch.zeros(current_batch_size)

            # make it cuda Tensor
            x_, y_real_, y_fake_ = Variable(x_.cuda()), Variable(y_real_.cuda()), Variable(y_fake_.cuda())

            # run real input on Discriminator
            D_result_real = net.D(x_)
            D_loss_real = net.BCE_loss(D_result_real, y_real_)

            # run Generator input on Discriminator
            z1_ = torch.Tensor(current_batch_size, net.z_size).uniform_(-1, 1)
            z1_ = Variable(z1_.cuda())
            x_fake = net.G(z1_)
            D_result_fake = net.D(x_fake)
            D_loss_fake = net.BCE_loss(D_result_fake, y_fake_)

            D_loss = D_loss_real + D_loss_fake

            # optimize Discriminator
            net.D.zero_grad()
            D_loss.backward()
            net.D_opt.step()

            '''
            Train in Generator
            '''
            z2_ = torch.Tensor(current_batch_size, net.z_size).uniform_(-1, 1)
            y_ = torch.ones(current_batch_size)
            z2_, y_ = Variable(z2_.cuda()), Variable(y_.cuda())
            G_result = net.G(z2_)
            D_result_fake2 = net.D(G_result)
            G_loss = net.BCE_loss(D_result_fake2, y_)

            net.G.zero_grad()
            G_loss.backward()
            net.G_opt.step()

            if step % print_every == 0:
                losses.append((D_loss.data[0], G_loss.data[0]))

                print("Epoch {}/{}...".format(e + 1, epochs),
                      "Discriminator Loss: {:.4f}...".format(D_loss.data[0]),
                      "Generator Loss: {:.4f}".format(G_loss.data[0]))

                # Sample from generator as we're training for viewing afterwards
        image_fn = './assets/epoch_{:d}_pytorch.png'.format(e)
        image_title = 'epoch {:d}'.format(e)
        save_generator_output(net.G, fixed_z, image_fn, image_title)

    return losses

def main():
    assets_dir = './assets/'
    if not os.path.isdir(assets_dir):
        os.mkdir(assets_dir)

    '''
    Parameters
    '''
    x_size = 28 * 28
    z_size = 100
    epochs = 30
    batch_size = 128
    learning_rate = 0.002
    data_loc = '../data_set/MNIST_data'

    # build network
    gan_net = GAN(x_size, z_size, learning_rate)

    # training
    start_time = time.time()
    losses = train(gan_net, epochs, batch_size, data_loc)
    end_time = time.time()
    total_time = end_time - start_time
    print('Elapsed time: ', total_time)
    # 30 epochs: 183.71

    fig, ax = plt.subplots()
    losses = np.array(losses)
    plt.plot(losses.T[0], label='Discriminator', alpha=0.5)
    plt.plot(losses.T[1], label='Generator', alpha=0.5)
    plt.title("Training Losses")
    plt.legend()
    plt.savefig('./assets/losses_pytorch.png')

    # create animated gif from result images
    images = []
    for e in range(epochs):
        image_fn = './assets/epoch_{:d}_pytorch.png'.format(e)
        images.append(imageio.imread(image_fn))
    imageio.mimsave('./assets/by_epochs_pytorch.gif', images, fps=3)

if __name__ == '__main__':
    main()