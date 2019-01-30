# Copyrights. All rights reserved.
# ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE, Switzerland,
# Space Center (eSpace), 2018
# See the LICENSE.TXT file for more details.

import os
import pkg_resources
import tempfile

from torch import optim
from torch.optim import lr_scheduler
from torch.utils import data

from practical_deep_stereo import flyingthings3d_dataset
from practical_deep_stereo import loss
from practical_deep_stereo import pds_network
from practical_deep_stereo import trainer
from practical_deep_stereo import transforms


FOLDER_WITH_FRAGMENT_OF_FLYINGTHINGS3D_DATASET = \
 pkg_resources.resource_filename(__name__, "data/flyingthings3d")


def _initialize_parameters():
    training_set, validation_set = \
        flyingthings3d_dataset.FlyingThings3D.training_split(
            FOLDER_WITH_FRAGMENT_OF_FLYINGTHINGS3D_DATASET,
                number_of_validation_examples=1)
    training_set.append_transforms(
        [transforms.CentralCrop(crop_height=64, crop_width=64)])
    validation_set.append_transforms(
        [transforms.CentralCrop(crop_height=64, crop_width=64)])
    training_set_loader = data.DataLoader(
        training_set,
        batch_size=1,
        shuffle=True,
        num_workers=1,
        pin_memory=True)
    validation_set_loader = data.DataLoader(
        validation_set,
        batch_size=1,
        shuffle=False,
        num_workers=1,
        pin_memory=True)
    network = pds_network.PdsNetwork()
    network.set_maximum_disparity(63)
    optimizer = optim.RMSprop(network.parameters(), lr=1e-3)
    return {
        'network':
        network,
        'optimizer':
        optimizer,
        'criterion':
        loss.SubpixelCrossEntropy(),
        'learning_rate_scheduler':
        lr_scheduler.StepLR(optimizer, step_size=10, gamma=0.5),
        'training_set_loader':
        training_set_loader,
        'validation_set_loader':
        validation_set_loader,
        'end_epoch':
        2,
        'experiment_folder':
        tempfile.mkdtemp()
    }


def test_trainer():
    pds_trainer = trainer.PdsTrainer(_initialize_parameters())
    pds_trainer.train()
    assert len(pds_trainer._training_losses) == 2
    assert pds_trainer._current_epoch == 2
    checkpoint_file = os.path.join(pds_trainer._experiment_folder,
                                   '002_checkpoint.bin')
    pds_trainer = trainer.PdsTrainer(_initialize_parameters())
    pds_trainer.load_checkpoint(checkpoint_file)
    pds_trainer._current_epoch == 2
    pds_trainer._end_epoch = 3
    pds_trainer.train()
    assert len(pds_trainer._training_losses) == 3
    assert pds_trainer._current_epoch == 3
    assert pds_trainer._training_losses[0] > pds_trainer._training_losses[2]
