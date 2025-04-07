# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Lionel Untereiner
from PIL import Image
from PIL import ImageChops


def image_pixel_differences( base_image_path, compare_image_path ):
    """
    Calculates the bounding box of the non-zero regions in the image.
    :param base_image: target image to find
    :param compare_image:  set of images containing the target image
    :return: True is the L1 value between each image is identitic,
     False otherwise
    """

    base_image = Image.open( base_image_path )
    compare_image = Image.open( compare_image_path )

    diff = ImageChops.difference( base_image, compare_image )
    if diff.getbbox():
        return False
    else:
        return True
