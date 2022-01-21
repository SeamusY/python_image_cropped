from pyimagesearch.transfrom import four_point_transform
from skimage.filters import threshold_local
import cv2
import imutils
import os
import boto3

def lambda_handler(event, context):
    event['queryStringParameters']["message"]
    file_name = event["body"]["fileName"]
    file = event["body"]["file"]
    phoneNumber = event["body"]["fileName"].split("---")[-1]
    lambda_client = boto3.client('lambda')
    cognito = boto3.client('cognito-idp')
    cognitoUser = cognito.list_users(
        UserPoolId=os.environ['aws_userpool_id'],
        Limit=1,
        Filter='phone_number="{}"'.format(phoneNumber)
    )

    if cognitoUser["Users"] == []:
        return {
            "errorCode": 400,
            "errorMessage": "No User Found",
            "errorType": "Runtime.ImportModuleError"
        }

    image = cv2.imread(file) # Incoming image
    ratio = image.shape[0]/500.0
    orig = image.copy()
    image = imutils.resize(image, height=500)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5,5), 0)
    edged = cv2.Canny(gray, 75, 200)

    # print("STEP 1:  Edge Detection") # Removed 
    cv2.imshow("Image", image) # Removed 
    cv2.imshow("Edged", edged) # Removed 
    cv2.waitKey(0) # Removed 
    cv2.destroyAllWindows() # Removed 

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

    # Show the contour (outline) of the piece of paper

    # print("STEP 2:  Find contours of paper")
    outerEdge = [screenCnt]
    print("Outer edge" , outerEdge)
    cv2.drawContours(image, outerEdge, -1, (0,255,0), 2)
    cv2.imshow("Outline", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    # Apply the four point transform to obtain a top-down view of the original image

    warped = four_point_transform(orig, screenCnt.reshape(4, 2) * ratio)

    # Convert the warped image to gray scale, then threshold it to give it that 'black and white' paper effect
    warped = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
    T = threshold_local(warped, 11, offset=10, method="gaussian")
    warped = (warped > T).astype("uint8") * 255

    Path = 'tmp/{}'.format(file_name)
    cv2.imshow("Scanned", imutils.resize(warped, height=650)) # once uploaded, rename the file the the original convention.
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    cv2.imwrite(Path, warped)
    # os.remove(Path) #After upload

