import numpy as np
import argparse
import cv2 as cv
import subprocess
import time
import os
from yolo_utils import infer_image, show_image
import subprocess
from gtts import gTTS 
from pydub import AudioSegment
from pathlib import Path
from pygame import mixer
from tempfile import TemporaryFile

AudioSegment.converter = "C:/FFmpeg/bin/ffmpeg.exe"
AudioSegment.ffprobe = "C:/FFmpeg/bin/ffprobe.exe"
#AudioSegment.ffmpeg = "C:/Users/Lenovo/Documents/Capstone/ffmpeg-4.3.1-win64-static/bin/ffmpeg.exe"

FLAGS = []

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('-m', '--model-path',
		type=str,
		default='./yolov3-coco/',
		help='The directory where the model weights and \
			  configuration files are.')

    parser.add_argument('-w', '--weights',
		type=str,
		default='./yolov3-coco/yolov3.weights',
		help='Path to the file which contains the weights \
			 	for YOLOv3.')

    parser.add_argument('-cfg', '--config',
		type=str,
		default='./yolov3-coco/yolov3.cfg',
		help='Path to the configuration file for the YOLOv3 model.')

    parser.add_argument('-i', '--image-path',
		type=str,
		help='The path to the image file')

    parser.add_argument('-v', '--video-path',
		type=str,
		help='The path to the video file')


    parser.add_argument('-vo', '--video-output-path',
		type=str,
        default='./output.avi',
		help='The path of the output video file')
    parser.add_argument('-l', '--labels',
		type=str,
		default='./yolov3-coco/coco-labels',
		help='Path to the file having the \
					labels in a new-line seperated way.')

    parser.add_argument('-c', '--confidence',
		type=float,
		default=0.5,
		help='The model will reject boundaries which has a \
				probabiity less than the confidence value. \
				default: 0.5')

    parser.add_argument('-th', '--threshold',
		type=float,
		default=0.3,
		help='The threshold to use when applying the \
				Non-Max Suppresion')

    parser.add_argument('--download-model',
		type=bool,
		default=False,
		help='Set to True, if the model weights and configurations \
				are not present on your local machine.')

    parser.add_argument('-t', '--show-time',
        type=bool,
        default=False,
        help='Show the time taken to infer each image.')

    FLAGS, unparsed = parser.parse_known_args()

    # Download the YOLOv3 models if needed
    if FLAGS.download_model:
        subprocess.call(['./yolov3-coco/get_model.sh'])

    # Get the labels
    labels = open(FLAGS.labels).read().strip().split('\n')

    # Intializing colors to represent each label uniquely
    colors = np.random.randint(0, 255, size=(len(labels), 3), dtype='uint8')

    # Load the weights and configutation to form the pretrained YOLOv3 model
    net = cv.dnn.readNetFromDarknet(FLAGS.config, FLAGS.weights)

    # Get the output layer names of the model
    layer_names = net.getLayerNames()
    layer_names = [layer_names[i[0] - 1] for i in net.getUnconnectedOutLayers()]
        
    # If both image and video files are given then raise error
    if FLAGS.image_path is None and FLAGS.video_path is None:
        print ('Neither path to an image or path to video provided')
        print ('Starting Inference on Webcam')

    # Do inference with given image
    if FLAGS.image_path:
        #ead the image
        try:
            img = cv.imread(FLAGS.image_path)
            height, width = img.shape[:2]
        except:
            raise 'Image cannot be loaded!\n\
                               Please check the path provided!'

        finally:
            img, _, _, _ = infer_image(net, layer_names, height, width, img, colors, labels, FLAGS)
            show_image(img)

    elif FLAGS.video_path:
        #ead the video
        try:
            vid = cv.VideoCapture(FLAGS.video_path)
            height, width = None, None
            writer = None
        except:
            raise 'Video cannot be loaded!\n\
                                  Please check the path provided!'

        finally:
            while True:
                grabbed, frame = vid.read()

                #g if the complete video is read
                if not grabbed:
                    break
                
                if width is None or height is None:
                    height, width = frame.shape[:2]

                frame, _, _, _, _ = infer_image(net, layer_names, height, width, frame, colors, labels, FLAGS)

                if writer is None:
                    #the video writer
                    fourcc = cv.VideoWriter_fourcc(*"MJPG")
                    writer = cv.VideoWriter(FLAGS.video_output_path, fourcc, 30, 
						            (frame.shape[1], frame.shape[0]), True)


                writer.write(frame)

            print ("[INFO] Cleaning up...")
            writer.release()
            vid.release()


    else:
        #infer real-time on webcam
        count = 0
        tts_count = 0
        vid = cv.VideoCapture(0)
        while True:
            tts_count+= 1
            _, frame = vid.read()
            height, width = frame.shape[:2]
            if count == 0:
                frames, boxes, confidences, classids, idxs, centers = infer_image(net, layer_names, \
		    						height, width, frame, colors, labels, FLAGS)
                count += 1
            else:
                frames, boxes, confidences, classids, idxs, centers = infer_image(net, layer_names, \
		    						height, width, frame, colors, labels, FLAGS, boxes, confidences, classids, idxs, infer=False)
                count = (count+1) % 6
            
            texts = []
            (H,W) = frame.shape[:2]
			#ensure at least one detection exists
            if len(idxs) > 0 and centers != None:
				# loop over the indexes we are keeping
                for i in idxs.flatten():
                    centerX, centerY = centers[i][0], centers[i][1]
                    if centerX <= W/3:
                        W_pos = "left "
                    elif centerX <= (W/3 * 2):
                        W_pos = "center "
                    else:
                        W_pos = "right "
					
                    if centerY <= H/3:
                        H_pos = "top "
                    elif centerY <= (H/3 * 2):
                        H_pos = "mid "    					
                    else:
                        H_pos = "bottom "
                    texts.append(H_pos + W_pos + labels[classids[i]])
            
                #print('Came out of loop')
                print(texts)
                if texts:
                    description = ', '.join(texts)
                    tts =gTTS(description, lang='en')
                    #sf = TemporaryFile()
                    my_file = "C:/Users/Lenovo/Documents/Capstone/YOLOv3-Object-Detection-with-OpenCV-master/mp31/tts" + str(tts_count) + ".mp3"
                    #print("tts" + str(tts_count) + ".mp3")
                    tts.save(my_file)
                    mixer.pre_init(22100, -16, 2, 64)
                    mixer.init()
                    mixer.music.load(my_file)
                    mixer.music.play()
                    time.sleep(1)
                #os.remove(my_file)
                    
    
            #print(texts)
            cv.imshow('webcam', frame)

            if cv.waitKey(1) & 0xFF == ord('q'):
                break        
        vid.release()
        cv.destroyAllWindows()
        os.remove(my_file)
