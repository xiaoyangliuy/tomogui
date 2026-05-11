import numpy as np


def sample_patch_corner(mask, window_size, num_windows):
    sample_patch_probs = (mask / mask.sum()).reshape((-1, 1)).squeeze().astype(np.float64)
    grid_indices = np.where(np.random.multinomial(1, sample_patch_probs / sample_patch_probs.sum(), num_windows))[1]
    patch_corners = []
    for grid_idx in grid_indices:
        grid_idx_ = []
        img_grids = np.indices(mask.shape)
        for d in range(len(list(mask.shape))):
            grid_idx_.append(img_grids[d].reshape((-1, 1)).squeeze()[grid_idx])
        if grid_idx_[-1] == 0:
            grid_idx_ = grid_idx_[:-1]
        patch_corner = [grid_idx_[i] - window_size // 2 for i in range(len(grid_idx_))]
        patch_corner = [max(0, pc) for pc in patch_corner]
        patch_corner = [min(pc, mask.shape[i] - window_size - 1) for i, pc in enumerate(patch_corner)]
        patch_corner = tuple(patch_corner)
        patch_corners.append(patch_corner)
    return patch_corners
