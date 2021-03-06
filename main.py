import json
from pprint import pprint
from importlib import import_module

import utils


def main():
    # get training parameters
    with open('params.json') as f:
        gan_params = json.load(f)

    print('--params--')
    pprint(gan_params)

    dataset_base_dir = './data_set'
    for param in gan_params:
        model_name = param["model-name"]
        epochs = int(param["epochs"])
        mnist_type = param["mnist-type"]
        mnist = utils.get_mnist(dataset_base_dir, mnist_type)

        print('Training {:s} with epochs: {:d}, dataset: {:s}'.format(model_name, epochs, mnist_type))

        # get appropriate module and it's class to start training
        module_name = import_module(model_name)
        gan_class = getattr(module_name, model_name.upper())
        net = gan_class(model_name, mnist_type, mnist, epochs)
        net.train()

    return


if __name__ == '__main__':
    main()
