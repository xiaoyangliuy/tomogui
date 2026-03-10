import time
import torch
import numpy as np
from pathlib import Path
from PIL import Image
from tomogui._tomocor_infer._utils import sample_patch_corner
from tomogui._tomocor_infer.model_archs import ClassificationModel, _make_dinov2_model


def inference_pipeline(args, img_cache, center_of_rotation_cache, out_dir):
    use_8bits = args.infer_use_8bits
    downsample_factor = args.infer_downsample_factor
    num_windows = args.infer_num_windows
    seed_number = args.infer_seed_number
    model_path = args.infer_model_path
    multi_instances = num_windows > 1
    sz = args.infer_window_size
    np.random.seed(seed_number)
    device = torch.device('cuda') if torch.cuda.is_available() else 'cpu'
    print(f'inference device: {device}  (cuda available: {torch.cuda.is_available()})')

    model_ = _make_dinov2_model()
    model = ClassificationModel(model_, embed_dim=model_.embed_dim, num_windows=num_windows, multi_instances=multi_instances)
    states = torch.load(model_path, map_location='cpu', weights_only=False)['state_dict']
    states = {(k.replace("module.", "") if "module." in k else k): v for k, v in states.items()}
    model.load_state_dict(states, strict=False)
    model.to(device)

    print('starting model inference...')
    t_start = time.time()

    if downsample_factor > 1:
        print(f"Resizing with downsample factor {downsample_factor}.")
    if use_8bits:
        print("Requantizing using 8 bits.")

    img_cache_ = []
    for img_ in img_cache:
        if downsample_factor > 1:
            pil_img = Image.fromarray(img_, mode='F')
            img_array = np.array(
                pil_img.resize(
                    (pil_img.size[0] // downsample_factor, pil_img.size[1] // downsample_factor),
                    Image.BILINEAR,
                ),
                dtype=np.float32,
            )
        else:
            img_array = img_.astype(np.float32)

        img_array = (img_array - img_array.min()) / (img_array.max() - img_array.min() + 1e-8)

        if use_8bits:
            img_array = (img_array * 255).astype(np.uint8).astype(np.float32) / 255.0

        img_cache_.append(img_array[None, ...])

    img_cache = np.concatenate(img_cache_, axis=0)

    row, col = img_cache.shape[1:]
    if multi_instances:
        x_coords, y_coords = np.meshgrid(np.arange(col) - (col - 1) / 2, np.arange(row) - (row - 1) / 2)
        mask = (x_coords ** 2 + y_coords ** 2) <= ((row - 1) / 2) ** 2
        patch_corners = sample_patch_corner(mask, sz, num_windows)
    else:
        patch_corner = (row // 2 - sz // 2, col // 2 - sz // 2)

    features = []
    for img_array in img_cache:
        if multi_instances:
            imgs = []
            for pc in patch_corners:
                img = img_array[pc[0]:pc[0] + sz, pc[1]:pc[1] + sz]
                img = torch.from_numpy(img).to(device=device, dtype=torch.float32).unsqueeze(0).unsqueeze(0).unsqueeze(0)
                imgs.append(img)
            sample = {'images': torch.cat(imgs, dim=1)}
        else:
            img = img_array[patch_corner[0]:patch_corner[0] + sz, patch_corner[1]:patch_corner[1] + sz]
            img = torch.from_numpy(img).to(device=device, dtype=torch.float32).unsqueeze(0).unsqueeze(0).unsqueeze(0)
            sample = {'images': img}
        with torch.no_grad():
            feature = model(sample)
        features.append(feature)

    print(f"done. Elapsed time: {time.time() - t_start:.1f} s.")

    features_all = torch.cat(features, dim=0).detach().cpu().numpy()
    scores = np.exp(features_all[:, 1]) / (np.exp(features_all[:, 0]) + np.exp(features_all[:, 1]))
    best_cors = [center_of_rotation_cache[i] for i in np.where(scores == scores.max())[0]]

    out_path = Path(out_dir) / 'center_of_rotation.txt'
    with open(out_path, 'a') as f:
        for cor in best_cors:
            f.write(f"{cor:.1f}\n")
