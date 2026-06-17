import cv2

def video_play(videos):

    video_list = videos
    tempList = []
    for i in video_list:
        i = 'Videos/' + i
        temp = cv2.VideoCapture("{0}.mp4".format(i))
        tempList.append(temp)

    return tempList




