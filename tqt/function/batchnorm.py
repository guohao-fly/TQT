"""
Provide quantilized form of torch.nn.modules.batchnorm 
"""

import torch
import torch.nn as nn
import torch.nn.functional as F

from .number import qsigned


class BatchNorm2d(nn.BatchNorm2d):
    def __init__(self,
                 num_features,
                 eps=1e-5,
                 momentum=0.1,
                 affine=True,
                 track_running_stats=True,
                 weight_bit_width=8,
                 bias_bit_width=16,
                 retrain=True):
        super().__init__(num_features, eps, momentum, affine,
                         track_running_stats)

        self.weight_bit_width = weight_bit_width
        self.bias_bit_width = bias_bit_width
        self.retrain = retrain
        if retrain is True:
            self.weight_log2_t = nn.Parameter(torch.Tensor(1))
            self.bias_log2_t = nn.Parameter(torch.Tensor(1))
            self.init_param(retrain)
        else:
            self.weight_log2_t = torch.Tensor(1)
            self.bias_log2_t = torch.Tensor(1)
            self.init_param(retrain)

    def init_param(self, retrain):
        pass

    def bn_forward(self, input):
        if self.affine is True:
            weight = qsigned(self.weight, self.weight_log2_t,
                                self.weight_bit_width)
            bias = qsigned(self.bias, self.bias_log2_t,
                            self.bias_bit_width)
            output = F.batch_norm(input,
                                    running_mean=self.running_mean,
                                    running_var=self.running_var,
                                    weight=weight,
                                    bias=bias)
        else:
            output = F.batch_norm(input,
                                    running_mean=self.running_mean,
                                    running_var=self.running_var)
        return output

    def forward(self, input):
        return self.bn_forward(input)
