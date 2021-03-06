# encoding=utf-8
# 在Z方向进行预处理，做扫描侧面看的视图

import numpy as np
import nibabel as nib
import matplotlib.pyplot as plt
import scipy.ndimage
from tqdm import tqdm
from config import *
from util import *
from lib.threshold_function_module import windowlize_image

'''
测试预处理代码，包含脚手架代码，保存成nii文件
写降噪和增强的代码
'''
volumes = listdir(volumes_path)
labels = listdir(labels_path)

if not os.path.exists(zpreprocess_path):
	os.makedirs(zpreprocess_path)

pbar=tqdm(range(len(labels)) ,desc="数据处理中")
for i in range(len(labels)):

	pbar.set_postfix(filename=labels[i].rstrip(".nii"))
	pbar.update(1)

	print(volumes[i], labels[i])

	volf = nib.load(os.path.join(volumes_path, volumes[i]))
	labf = nib.load(os.path.join(labels_path, labels[i]))

	header = volf.header.structarr
	save_info(volumes[i], header, 'vol_info.csv')

	volume = volf.get_fdata()
	label = labf.get_fdata()

# 	volume=np.clip(volume,-1024,1024)
	# volume = windowlize_image(volume, 500, 30)
	# label = clip_label(label, 1)  # 这个在训练的时候都可以做，尽量做一个通用的插值数据集之后更灵活

	spacing = [1, 1, 1]
	pixdim = [header['pixdim'][1], header['pixdim'][2], header['pixdim'][3]]  # pixdim 是这张 ct 三个维度的间距
	ratio = [pixdim[0]/spacing[0], pixdim[1]/spacing[1], pixdim[2]/spacing[2]]
	ratio = [1, 1, ratio[2]]

	volume=scipy.ndimage.interpolation.zoom(volume,ratio,order=3)
	label=scipy.ndimage.interpolation.zoom(label,ratio,order=0)

	# for ind in range(512):
	# 	plt.imshow(volume[ind, :, :])
	# 	plt.show()
	# 	plt.close()

	# if label.sum() < 32:
	# 	continue

	# bb_min, bb_max = get_bbs(label)
	# label = crop_to_bbs(label, bb_min, bb_max)[0]
	# volume = crop_to_bbs(volume, bb_min, bb_max)[0]
	#
	label = pad_volume(label, 512, 0)  # NOTE: 注意这里使用 0
	volume = pad_volume(volume, 512, -1024)
	print(label.shape)
	volume = volume.astype(np.float16)
	label = label.astype(np.int8)
	# volume = np.ones( [512, 512, 615])
	# label = np.ones([512, 512, 615])

	for frame in range(1, volume.shape[0]-1):
		if np.sum(label[frame ,: ,:]) > 128:
			vol=volume[frame-1: frame+2, :, :]
			lab=label[frame, :, :]
			lab = lab.reshape([1, lab.shape[0], lab.shape[1]])

			vol = vol[:, :, 0:512]
			lab = lab[:, :, 0:512]
			# print(vol.shape)
			# print(lab.shape)
			data=np.concatenate((vol, lab), axis=0)
			file_name = "lits{}-{}.npy".format(volumes[i].rstrip(".nii").lstrip("volume"),frame)
			np.save(os.path.join(zpreprocess_path, file_name),data )

pbar.close()
