#
# Implementation of the image registration algorithm by Conover et al. [2015]
#
# This code was adapted from an implementation of the same algorithm by
#   Dr. Matthias Alfeld (TU Delft)
#

import numpy as np

from scipy import optimize
from scipy import interpolate

import cv2

import functools
import time

# https://stackoverflow.com/a/20924212/14647075
def timeit(func):
    @functools.wraps(func)
    def new_func(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed_time = time.time() - start_time
        print('function [{}] finished in {} ms'.format(
            func.__name__, int(elapsed_time * 1_000)))
        return result
    return new_func


def lowpass(order, image, axis):
    """
    Applies a lowpass filter to the given image and returns the result.

    Parameters
    ----------
    order : int
            The order of the filter
    image : (N, M, P) array_like
            Image to apply the filter to
    axis : int
           0 => apply over the x-axis, 1 => over the y-axis
    
    Returns
    -------
    lowpassed : (N, M, K) array_like
                The lowpassed input image
    """
    d1 = 2 * order if axis == 0 else 1
    d2 = 2 * order if axis == 1 else 1
    
    kernel = np.full((d1, d2), 1 / (d1 * d2), dtype=np.float32)
    return cv2.filter2D(image.astype(np.float32), -1, kernel)


def highpass(order, image, axis):
    """
    Applies a highpass filter to the given image and returns the result.

    Parameters
    ----------
    order : int
            The order of the filter
    image : (N, M, K) array_like
            Image to apply the filter to
    axis : int
           0 => apply over the x-axis, 1 => over the y-axis
    
    Returns
    -------
    lowpassed : (N, M, K) array_like
                The highpassed input image
    """
    d1 = 2 * order if axis == 0 else 1
    d2 = 2 * order if axis == 1 else 1
    
    kernel = np.full((d1, d2), 1 / (d1 * d2), dtype=np.float32)
    for i in range(d1 * d2 // 2):
        if axis == 0:
            kernel[i,:] = -kernel[i,:]
        else:
            kernel[:,i] = -kernel[:,i]
    return cv2.filter2D(image.astype(np.float32), -1, kernel)


# @timeit
def compute_modulus(image, order):
    """
    Computes the modulus of the wavelet transform of an image as
    described in Section 3.1 of the work by Conover et al. [2015].

    The size of the detected features correlates to the given order
    of the filter.

    Parameters
    ----------
    image : (N, M) array_like
            Image to compute the modulus of
    order : int
            The order of the filter

    Returns
    -------
    wavelet : (N, M) array_like
              Modulus of `image`
    """
    merged = cv2.magnitude(
        highpass(order, lowpass(order, image, axis=1), axis=0)
            .astype(dtype=np.float32, subok=True, copy=False),
        lowpass(order, highpass(order, image, axis=1), axis=0)
            .astype(dtype=np.float32, subok=True, copy=False))

    return merged


# @timeit
def identify_control_points(image, windowsize):
    """
    Identifies the control-points from the modulus of the wavelet
    transform of an image by finding all the local maxima in
    neighbourhoods of size `windowsize`.

    Parameters
    ----------
    image : (N, M) array_like
            Modulus of an image
    windowsize : int
                 Size of the square neighbourhood around each maximum
    
    Returns
    -------
    xys : (K, 2) array_like
             List of the x and y coordinates of each identified control-point
    """
    # https://stackoverflow.com/a/42647989/14647075

    kernel = np.ones((windowsize, windowsize), dtype=np.uint8)
    kernel[windowsize // 2, windowsize // 2] = 0
    
    pairs = np.squeeze(
        cv2.findNonZero(
            cv2.compare(
                image,
                cv2.dilate(image, kernel),
                cv2.CMP_GT
            )
        )
    )

    return pairs if len(pairs.shape) != 0 else []


# @timeit
def approximate_transformation(reference, template, template_mask = None):
    """
    Attempts to find an initial transformation of the template to the reference
    using SIFT.

    Parameters
    ----------
    reference : (N, M, P) array_like
                Reference image, pixel values should be between 0 and 1
    template : (Q, R, S) array_like
               Template image, pixel values should be between 0 and 1
    template_mask : (Q, R) array_like
                    Mask for the template image, features will only be found
                    where the mask is 255.
    
    Returns
    -------
    transformation : (2, 3) array_like
                     Returns a matrix representing a 2D affine transformation.
    """
    reference_norm = (reference - reference.min()) / (reference.max() - reference.min())
    template_norm = (template - template.min()) / (template.max() - template.min())

    reference_norm = (reference_norm * 255).astype(dtype=np.uint8, subok=True, copy=False)
    template_norm = (template_norm * 255).astype(dtype=np.uint8, subok=True, copy=False)

    sift = cv2.SIFT.create(0, 3, 0.04, 10, 1.6) # Using Lowe's parameters
    kp_ref, desc_ref = sift.detectAndCompute(reference_norm, None)
    kp_temp, desc_temp = sift.detectAndCompute(template_norm, template_mask)

    bf_matcher = cv2.BFMatcher.create()
    matches = sorted(
        bf_matcher.knnMatch(desc_temp, desc_ref, k=3),
        key = lambda match: match[0].distance / match[1].distance
    )
    matches = matches[:np.clip(int(len(matches) * 0.15), 8, 48)]

    if len(matches) < 2:
        transform = np.array([
            [1, 0, 0],
            [0, 1, 0]
        ], dtype=np.float32)
    else:
        transform, _ = cv2.estimateAffine2D(
            np.array([ kp_temp[match[0].queryIdx].pt for match in matches ]),
            np.array([ kp_ref[match[0].trainIdx].pt for match in matches ])
        )
    
    return transform


def transform_template_affine(reference, template, matrix):
    """
    Transforms the template image according to the matrix and takes a
    subsection of the relevant part of the referece image.

    Parameters
    ----------
    reference : (N, M, P) array_like
                Reference image
    template : (Q, R, S) array_like
               Template image
    matrix : (2, 3) array_like
             Matrix representing a 2D affine transformation.
    
    Returns
    -------
    new_reference : (T, U, V) array_like
                    Subsection of the reference image where new_template should
                    roughly be aligned
    new_template : (T, U, V) array_like
                   Transformed template image
    """
    width = int(np.dot(matrix[0], (template.shape[1], template.shape[0], 1)))
    height = int(np.dot(matrix[1], (template.shape[1], template.shape[0], 1)))

    offset = matrix[:, 2]
    new_shape = (
        template.shape[0] * matrix[1, 1],
        template.shape[1] * matrix[0, 0]
    )

    template_minx = int(max(0, offset[0]))
    template_miny = int(max(0, offset[1]))

    new_template = cv2.warpAffine(
        template.astype(np.float32),
        matrix,
        (width, height)
    ).astype(
        dtype=np.float32, subok=True, copy=False
    )[
        template_miny:int(min(reference.shape[0], offset[1] + new_shape[0])),
        template_minx:int(min(reference.shape[1], offset[0] + new_shape[1]))
    ]

    new_reference = reference.astype(np.float32)[
        template_miny:template_miny+new_template.shape[0],
        template_minx:template_minx+new_template.shape[1]
    ]

    return new_reference, new_template


def upscale_region(image, center, halfsize, factor):
    """
    Upscales the region of size `2 * halfsize` centered around
    `center` by the given factor.

    The resize method uses bicubic interpolation.

    Parameters
    ----------
    image : (N, M, P) array_like
            Image from which to extract and upscale
    center : (scalar, scalar)
             The center coordinates of the region
    halfsize : (scalar, scalar)
               Half of the width and height of the region
    factor : scalar
             Resize factor
    
    Returns
    -------
    image : (K, L, P) array_like
            The upscaled extracted region from the input image
    """
    minx = int(max(0, center[0] - halfsize[0]))
    miny = int(max(0, center[1] - halfsize[1]))
    maxx = int(min(image.shape[1], center[0] + halfsize[0] + 1))
    maxy = int(min(image.shape[0], center[1] + halfsize[1] + 1))
    
    if maxx <= minx or maxy <= miny:
        return None
    
    return cv2.resize(
        image[miny:maxy, minx:maxx],
        None, fx=factor, fy=factor,
        interpolation=cv2.INTER_CUBIC)


# @timeit
def find_control_point_pairs(reference, template, control_point_xys, search_region_size, control_point_region_size, scale_factor):
    """
    Finds the control-point pairs between the reference and template
    images.

    Parameters
    ----------
    reference : (N, M, 4) array_like
                The reference image
    template : (L, K, 4) array_like
               The template image
    control_point_xys : (P, 2)[]
                        The x and y coordinates of the
                        control-points relative to the template image
    search_region_size : int
                         The size of the regions around the
                         control-points in the reference image
    control_point_region_size : int
                                The size of the regions around the
                                control-points in the template image
    scale_factor : scalar
                   The factor with which to scale the regions around
                   the control-points
    
    Returns
    -------
    keypoints_reference,
    keypoints_template : (Q, 2) array_like
                         The sub-pixel x and y coordinates of the keypoints
                         found in the reference and template images
                         respectively, points of the same index in both arrays
                         are pairs
    """
    keypoints_reference = []
    keypoints_template  = []

    # Find the optimal sizes for both images
    #   Reference first
    optimal_width  = cv2.getOptimalDFTSize(reference.shape[1] + 10)
    optimal_height = cv2.getOptimalDFTSize(reference.shape[0] + 10)
    reference = cv2.copyMakeBorder(
        reference,
        0, optimal_height - reference.shape[0],
        0, optimal_width  - reference.shape[1],
        cv2.BORDER_CONSTANT,
        value = 0
    ).astype(dtype=np.float32, subok=True, copy=False)
    
    #  Template next
    optimal_width  = cv2.getOptimalDFTSize(template.shape[1] + 10)
    optimal_height = cv2.getOptimalDFTSize(template.shape[0] + 10)
    template = cv2.copyMakeBorder(
        template,
        0, optimal_height - template.shape[0],
        0, optimal_width  - template.shape[1],
        cv2.BORDER_CONSTANT,
        value = 0
    ).astype(dtype=np.float32, subok=True, copy=False)
    

    # Calculate the full-scale phase images for both
    fft = cv2.dft(reference, flags = cv2.DFT_COMPLEX_OUTPUT)
    fft[:,:,0], fft[:,:,1] = cv2.polarToCart(
        None, cv2.phase(fft[:,:,0], fft[:,:,1]))
    ifft = cv2.idft(fft)
    reference = cv2.magnitude(ifft[:,:,0], ifft[:,:,1])

    fft = cv2.dft(template, flags = cv2.DFT_COMPLEX_OUTPUT)
    fft[:,:,0], fft[:,:,1] = cv2.polarToCart(
        None, cv2.phase(fft[:,:,0], fft[:,:,1]))
    ifft = cv2.idft(fft)
    template = cv2.magnitude(ifft[:,:,0], ifft[:,:,1])


    for x, y in control_point_xys:
        search_region = (
            upscale_region(
                reference,
                (x, y),
                (search_region_size, search_region_size),
                scale_factor))
        
        if search_region is None:
            continue
        
        control_point_region = (
            upscale_region(
                template,
                (x, y),
                (control_point_region_size, control_point_region_size),
                scale_factor))
        
        if control_point_region is None:
            continue
        
        if (search_region.shape[0] < control_point_region.shape[0]
            or search_region.shape[1] < control_point_region.shape[1]
        ):
            continue

        ccorr = cv2.matchTemplate(
            search_region,
            control_point_region,
            cv2.TM_CCORR_NORMED)
        
        maxval = ccorr.max()
        ccorr_no_max = ccorr[ccorr != maxval]
        std = ccorr_no_max.std()

        T1 = maxval >= 4 * std
        T2 = (ccorr_no_max.shape[0] > 0
            and maxval > (ccorr_no_max.max() + std))
        
        if T1 and T2:
            ty, tx = np.unravel_index(np.argmax(ccorr), ccorr.shape)

            accepted_point = (
                x + tx / scale_factor - (search_region_size - control_point_region_size),
                y + ty / scale_factor - (search_region_size - control_point_region_size)
            )
        
            keypoints_reference.append(accepted_point)
            keypoints_template.append((x, y))

    return (
        np.array(keypoints_reference),
        np.array(keypoints_template)
    )


def fit_bilinear(xdata, ydata, target_xdata, target_ydata, iteration_count = 20, threshold = 1 / 3):
    """
    Fits the 2D data to a 2D bilinear function.
    This function stops when any of the following is true:
      - The number of iterations has reached `iteration_count`
      - The number of points that fit the function with a certain threshold is
        less than 4
    The returned arrays are subsets of the input arrays with the same name.

    Parameters
    ----------
    xdata,
    ydata : (N, 2) array_like
            The input data for the x and y directions
    target_xdata,
    target_ydata : (N, 2) array_like
                   The ideal data for the x and y directions, the bilinear
                   function is fitted to approximate this data as closely as 
                   possible
    iteration_count : int
                      The maximum number of iterations
    threshold : scalar
                The target maximum disparity

    Returns
    -------
    fitness : scalar
              The last valid threshold value, lower is better
              Returns -1 if something went wrong
    point_count : int
                  The amount of points that fit the function with a threshold
                  of `fitness`
    xoptimal : (scalar)[] or None
               Set of parameters for the best mapping of x coordinates
    yoptimal : (scalar)[] or None
               Set of parameters for the best mapping of y coordinates
    """
    if len(xdata) <= 4 or len(ydata) <= 4:
        return -1, 0, None, None

    fitfunc = bilinear_function

    xydata = np.hstack((xdata, ydata))

    xoptimal, _ = optimize.curve_fit(fitfunc, xydata, target_xdata)
    yoptimal, _ = optimize.curve_fit(fitfunc, xydata, target_ydata)

    xdisparities = np.abs(fitfunc(xydata, *xoptimal) - target_xdata)
    ydisparities = np.abs(fitfunc(xydata, *yoptimal) - target_ydata)

    thresholds = np.geomspace(20, threshold, iteration_count)

    i = -1
    point_count = 0
    for threshold in thresholds:
        i += 1
        xindices = np.squeeze(np.where(xdisparities < threshold))
        yindices = np.squeeze(np.where(ydisparities < threshold))

        point_count = len(xindices)
        if len(xindices) <= 4 or len(yindices) <= 4:
            break

        good_xdata = xydata[np.hstack((xindices, xindices + len(xdata)))]
        good_ydata = xydata[np.hstack((yindices, yindices + len(ydata)))]

        xoptimal, _ = optimize.curve_fit(
            fitfunc, good_xdata, target_xdata[xindices], p0 = xoptimal)
        yoptimal, _ = optimize.curve_fit(
            fitfunc, good_ydata, target_ydata[yindices], p0 = yoptimal)

        xdisparities = np.abs(
            fitfunc(xydata, *xoptimal) - target_xdata)
        ydisparities = np.abs(
            fitfunc(xydata, *yoptimal) - target_ydata)
    
    
    if (threshold < 0
        or xoptimal is None
        or yoptimal is None
        or len(target_xdata) == 0
        or len(target_ydata) == 0
    ):
        return -1, 0, None, None
    
    return (
        thresholds[i],
        point_count,
        xoptimal,
        yoptimal
    )


def bilinear_function(xdata, a, b, c, d):
    """
    A basic bilinear function.

    Parameters
    ----------
    xdata : (N, 1) array_like
            The input x and y data stacked such that the x data is found in the
            [0, N / 2] range and the y data is found in [N / 2, N]
    a, b, c, d : scalar
               The four control points of the bilinear function
    
    Returns
    -------
    result : (N / 2, 1) array_like
             The values of the bilinear function with the given control points
             applied to the input data
    """
    # xdata should be normalized
    x = xdata[:xdata.shape[0] // 2]
    y = xdata[xdata.shape[0] // 2:]

    result = (a
            + b * x
            + c * y
            + d * x * y)
    return result


# @timeit
def conover(reference, template, mask = None, order = 3, windowsize = 12,
    search_region_size = 20, control_point_region_size = 12,
    scale_factor = 3,
    control_points = None,
    transform = None
):
    """
    Applies the algorithm described by Conover et al. in their 2015 paper.

    The resulting `aligned_template` is not the final aligned image.
    The final mapping takes a relatively long time, so it has been extracted
    into `deform_image`

    Parameters
    ----------
    reference : (N, M, 3) array_like
                Reference image
    template : (N, M, 3) array_like
               Template image
    mask : (N, M) array_like
           The mask applied to the template image
    order : int
            The order of the filter
    windowsize : int
                 Size of the square neighbourhood around each maximum
    search_region_size : (int, int)
                         The size of the regions around the
                         control-points in the reference image
    control_point_region_size : (int, int)
                                The size of the regions around the
                                control-points in the template image
    scale_factor : scalar
                   The factor with which to scale the regions around
                   the control-points
    
    Returns
    -------
    result : dict {
        fitness : scalar
                  The last valid threshold value, lower is better
                  Returns -1 if something went wrong
        point_count : int
                      The amount of points that fit the function with a threshold
                      of `fitness`
        transform : (2, 3) array_like
                    Matrix representing a 2D affine transformation.
        xoptimal : (scalar)[]
                   Set of parameters for the best mapping of x coordinates
        yoptimal : (scalar)[]
                   Set of parameters for the best mapping of x coordinates
        keypoints_reference,
        keypoints_template : (N, 2) array_like
                             The sub-pixel x and y coordinates of the keypoints
                             found in the reference and template images
                             respectively, points of the same index in both arrays
                             are pairs
        aligned_template : (M, P, 3) array_like
                           Roughly aligned template image
    }
    """
    # Apply the algorithm, each step in the paper roughly corresponds to
    # a function
    result = {
        "fitness": -1,
        "transform": None,
        "xoptimal": None,
        "yoptimal": None,
        "keypoints_reference": None,
        "keypoints_template": None,
        "aligned_template": None,
        "point_count": 0
    }

    if control_points is None:
        wavelet = compute_modulus(template, order)
        control_points = identify_control_points(wavelet, windowsize)
    
    if len(control_points) <= 0:
        return result

    if transform is None:
        transform = approximate_transformation(
            reference,
            template,
            np.uint8(255 - mask * 255)
        )
    result["transform"] = transform

    new_reference, new_template = transform_template_affine(
        reference, template, transform)
    result["aligned_template"] = new_template
    
    if (0 in new_reference.shape[:3]
        or 0 in new_template.shape[:3]
    ):
        transform = np.array([
            [1, 0, 0],
            [0, 1, 0]
        ], dtype=np.float32)
        result["transform"] = transform

        new_reference, new_template = transform_template_affine(
            reference, template,  transform)

    if (0 in new_reference.shape[:3]
        or 0 in new_template.shape[:3]
    ):
        return

    control_points = np.dot(
        control_points,
        transform[:, :2].T
    )
    
    keypoints_reference, keypoints_template = find_control_point_pairs(
        new_reference[:,:,:3].sum(2),
        new_template[:,:,:3].sum(2),
        control_points,
        search_region_size,
        control_point_region_size,
        scale_factor
    )

    if (len(np.squeeze(keypoints_reference)) == 0
        or len(np.squeeze(keypoints_template)) == 0
    ):
        return result
    
    result["keypoints_reference"] = keypoints_reference
    result["keypoints_template"] = keypoints_template

    kp_temp_norm = keypoints_template / new_template.shape[:2][::-1] - 0.5

    fitness, point_count, xoptimal, yoptimal = fit_bilinear(
        kp_temp_norm[:, 0],
        kp_temp_norm[:, 1],
        keypoints_reference[:, 0],
        keypoints_reference[:, 1],
        threshold = 1 / 5,
        iteration_count = 20
    )

    result["fitness"] = fitness
    result["point_count"] = point_count
    result["xoptimal"] = xoptimal
    result["yoptimal"] = yoptimal

    return result


# @timeit
def deformImage(image, coeffx, coeffy):
    """
    Deforms the image by using bilinear maps defined by the coeffx and coeffy.

    Parameters
    ----------
    image : (N, M, {3, 4}) array_like
            The image to deform, can be RGB or RGBA
    coeffx : (scalar)[]
             The parameters for the bilinear map for the x coordinates
    coeffy : (scalar)[]
             The parameters for the bilinear map for the y coordinates

    Returns
    -------
    result : (N, M, 4) array_like
             The deformed image
    """
    image = image.astype(np.float32)

    width  = image.shape[1]
    height = image.shape[0]

    if image.shape[2] == 3:
        image = cv2.cvtColor(image, cv2.COLOR_RGB2RGBA)

    result = np.zeros((height, width, 4))

    grid_x, grid_y = np.meshgrid(
        np.arange(width), np.arange(height))

    grid_x_norm = (grid_x / width - 0.5).flatten()
    grid_y_norm = (grid_y / height - 0.5).flatten()

    apr_x = bilinear_function(
        np.hstack((grid_x_norm, grid_y_norm)), *(coeffx))

    apr_y = bilinear_function(
        np.hstack((grid_x_norm, grid_y_norm)), *(coeffy))

    for j in range(result.shape[2]):
        interpolated = interpolate.griddata(
            np.vstack((apr_x.flatten(), apr_y.flatten())).T,
            image[:,:,j].flatten(),
            np.vstack((grid_x.flatten(), grid_y.flatten())).T
        )

        interpolated = interpolated.reshape(result.shape[:2])
        interpolated[np.isnan(interpolated)] = 0
        result[:,:,j] = interpolated
    
    return result
