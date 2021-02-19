import torch
import torch.nn as nn


def kl_divergence(ha, hb):
    r'''
        ans = J_{kl}(a,b)
    '''
    return torch.sum(ha * torch.log(ha / hb))


def quantize_bins_and_expand(dist, quant_bins):
    dist_len = dist.shape[0]
    width = torch.floor(1. * dist_len / quant_bins)
    dist_q = torch.zeros([quant_bins])
    dist_e = 0. * dist
    for i in range(quant_bins):
        if i != quant_bins - 1:
            dist_q[i] = dist[i * width:(i + 1) * width].sum()
            width_preserve = width - (dist[i * width:(i + 1) * width]
                                      == 0).sum()
            dist_e[i * width:(i + 1) * width] = dist_q[i] / width_preserve * (
                dist[i * width:(i + 1) * width] == 0)
        else:
            dist_q[i] = dist[i * width:].sum()
            width_preserve = width - (dist[i * width:] == 0).sum()
            dist_e[i * width:] = dist_q[i] / width_preserve * (dist[i * width:]
                                                               == 0)
    return dist_e


def entropy_calibration(model, bin_number=2048, cali_number=128):
    dist = model.hook_out.flatten().data
    dist = torch.histc(dist, bins=bin_number)
    bin_width = (dist.max() - dist.min()) / bin_number
    divergence = torch.zeros([bin_number]) * 1.0
    for i in range(cali_number, bin_number):
        ref_dist = dist[:i]
        outliers_count = dist[i:].sum()
        ref_dist[-1] += outliers_count
        ref_dist /= ref_dist.sum()
        can_dist = quantize_bins_and_expand(dist[:i], cali_number)
        can_dist /= can_dist.sum()
        divergence[i] = kl_divergence(ref_dist, can_dist)

    m, m_idx = torch.min(divergence[cali_number:], 0)
    threshold = dist.min() + (m_idx + cali_number + 0.5) * bin_width
    log2_t = torch.log2(threshold)
    model.acti_log2_t = log2_t