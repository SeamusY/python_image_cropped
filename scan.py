from pyimagesearch.transfrom import four_point_transform
from skimage.filters import threshold_local
import cv2
import imutils
import boto3
from botocore.exceptions import ClientError
import json

def lambda_handler(event, context):
    s3 = boto3.resource('s3')
    userId = event["requestContext"]["authorizer"]["claims"]["cognito:username"]
    file_name = event["body"]["fileName"]
    phoneNumber = event["body"]["fileName"].split("---")[2]
    file = event["body"]["file"]

    image = cv2.imread(file)
    ratio = image.shape[0]/500.0
    orig = image.copy()
    image = imutils.resize(image, height=500)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5,5), 0)
    edged = cv2.Canny(gray, 75, 200)

    # Find the contours in the edged image, keeping only the largest ones, and initialize the screen contour

    cnts = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    cnts = sorted(cnts, key=cv2.contourArea, reverse = True)[:5]

    # Loop over the contours

    for c in cnts:
        """
        Approximate the contour
        """
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)

        # If our approximated contour has four points, then we can assume that we have found out screen

        if len(approx) == 4:
            screenCnt = approx
            break

    # Apply the four point transform to obtain a top-down view of the original image

    warped = four_point_transform(orig, screenCnt.reshape(4, 2) * ratio)

    # Convert the warped image to gray scale, then threshold it to give it that 'black and white' paper effect
    warped = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
    T = threshold_local(warped, 11, offset=10, method="gaussian")
    warped = (warped > T).astype("uint8") * 255
    try:
        s3.meta.client.upload_file(warped, 'business-data-ae', 'public/backup/{}/{}/{}'.format(userId, phoneNumber, file_name))
        return json.dump({"statusCode": 200, "message": "Updated Files Success"})
    except ClientError as e:
        print("Error happened ", e)
        return json.dump({"statusCode": 400, "message": "Files failed to upload"})
    