import numpy as np
def rx_anomaly(hsi_img, guard_win, bg_win, mask = None):
	"""
	Widowed Reed-Xiaoli anomaly detector
		use local mean and covariance to determine pixel to background distance

	Inputs:
		hsi_image - n_row x n_col x n_band
		mask - binary image limiting detector operation to pixels where mask is true
	           if not present or empty, no mask restrictions are used
		guard_win - guard window radius (square,symmetric about pixel of interest)
		bg_win - background window radius

	8/7/2012 - Taylor C. Glenn - tcg@cise.ufl.edu
	5/5/2018 - Edited by Alina Zare
	10/1/2018 - Python Implementation by Yutai Zhou
	"""
	def pinv_matlab(A, tol, show = False):
		u, s, v = np.linalg.svd(A)
		r1 = np.argwhere(s > tol).shape[0]
		v = np.delete(v, list(range(r1,len(v))), axis = 1)
		u = np.delete(u, list(range(r1,len(u))), axis = 1)
		s = np.delete(s, list(range(r1,len(s))))
		s = 1 / s
		s = np.reshape(s,(len(s),1))
		# if show: print(tol)


		return (v * s.T) @ u.T

	n_row, n_col, n_band = hsi_img.shape
	n_pixels = n_row * n_col

	mask = np.ones((n_row, n_col)) if mask is None else mask

	# Create the mask
	mask_width = 1 + 2 * guard_win + 2 * bg_win
	half_width = guard_win + bg_win
	mask_rg = mask_width# 13

	b_mask = np.ones((mask_width, mask_width))
	b_mask[bg_win:b_mask.shape[0] - bg_win, bg_win:b_mask.shape[0] - bg_win] = False

	hsi_data = np.reshape(hsi_img, (n_pixels, n_band), order='F').T
	# run the detector (only on fully valid points)
	rx_img = np.zeros((n_row, n_col))

	for i in range(0, n_col - mask_width + 1):
		for j in range(0, n_row - mask_width + 1):
			row = j + half_width
			col = i + half_width

			if mask[row, col] is None: continue

			b_mask_img = np.zeros((n_row, n_col))
			b_mask_img[j:mask_rg + j, i:mask_rg + i] = b_mask #when i=j=1, j:mask_rg + j = 1:14
			b_mask_list = np.reshape(b_mask_img, (b_mask_img.size), order='F')
			# pull out background points
			bg = hsi_data[:, [int(m) for m in np.argwhere(b_mask_list == 1)]]

			# Mahlanobis distance
			covariance = np.cov(bg.T, rowvar=False)
			s = np.linalg.svd(covariance, compute_uv=False)
			# if i ==0 and j==0: np.linalg.pinv(covariance, rcond=np.max(covariance.shape)*np.spacing(np.float32(np.linalg.norm(s, ord=np.inf))))
			sig_inv = np.linalg.pinv(np.float32(covariance), rcond=np.max(covariance.shape)*np.spacing(np.float32(np.linalg.norm(s, ord=np.inf))))

			mu = np.mean(bg, 1)
			z = hsi_img[row, col, :] - mu
			z = np.reshape(z, (len(z), 1), order='F')

			rx_img[row, col] = z.T @ sig_inv @ z
			# if i==0 and j==0: print(sig_inv[:,0])

	return rx_img
