
# test to check that the client is receiving video frames from server  
import cv2
cap = cv2.VideoCapture("http://"your server ip address":12346")  # Replace with server details
while True:
    ret, frame = cap.read()
    if not ret:
        break
    cv2.imshow("Video Feed", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
cap.release()
cv2.destroyAllWindows()
