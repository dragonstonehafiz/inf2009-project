'''
This file is 
'''

import cv2
from edge_impulse_linux.image import ImageImpulseRunner

runner = None
modelfile = "model/test-image-linux-aarch64-v9.eim"

print('MODEL: ' + modelfile)

with ImageImpulseRunner(modelfile) as runner:
    try:
        model_info = runner.init()
        # model_info = runner.init(debug=True) # to get debug print out

        print('Loaded runner for "' + model_info['project']['owner'] + ' / ' + model_info['project']['name'] + '"')
        labels = model_info['model_parameters']['labels']
        videoCaptureDeviceId = 0

        camera = cv2.VideoCapture(videoCaptureDeviceId)
        ret = camera.read()[0]
        if ret:
            backendName = camera.getBackendName()
            w = camera.get(3)
            h = camera.get(4)
            print("Camera %s (%s x %s) in port %s selected." %(backendName,h,w, videoCaptureDeviceId))
            camera.release()
        else:
            raise Exception("Couldn't initialize selected camera.")

        next_frame = 0 # limit to ~10 fps here

        for img in runner.get_frames(videoCaptureDeviceId):

            # make two cuts from the image, one on the left and one on the right
            features_l, cropped_l = runner.get_features_from_image(img, 'left')
            features_r, cropped_r = runner.get_features_from_image(img, 'right')

            # classify both
            res_l = runner.classify(features_l)
            res_r = runner.classify(features_r)

            cv2.imwrite('debug_l.jpg', cv2.cvtColor(cropped_l, cv2.COLOR_RGB2BGR))
            cv2.imwrite('debug_r.jpg', cv2.cvtColor(cropped_r, cv2.COLOR_RGB2BGR))

            def print_classification(res, tag):
                if "classification" in res["result"].keys():
                    print('%s: Result (%d ms.) ' % (tag, res['timing']['dsp'] + res['timing']['classification']), end='')
                    for label in labels:
                        score = res['result']['classification'][label]
                        print('%s: %.2f\t' % (label, score), end='')
                    print('', flush=True)
                elif "bounding_boxes" in res["result"].keys():
                    print('%s: Found %d bounding boxes (%d ms.)' % (tag, len(res["result"]["bounding_boxes"]), res['timing']['dsp'] + res['timing']['classification']))
                    for bb in res["result"]["bounding_boxes"]:
                        print('\t%s (%.2f): x=%d y=%d w=%d h=%d' % (bb['label'], bb['value'], bb['x'], bb['y'], bb['width'], bb['height']))

                if "visual_anomaly_grid" in res["result"].keys():
                    print('Found %d visual anomalies (%d ms.)' % (len(res["result"]["visual_anomaly_grid"]), res['timing']['dsp'] + res['timing']['classification']))
                    for grid_cell in res["result"]["visual_anomaly_grid"]:
                        print('\t%s (%.2f): x=%d y=%d w=%d h=%d' % (grid_cell['label'], grid_cell['value'], grid_cell['x'], grid_cell['y'], grid_cell['width'], grid_cell['height']))

            print_classification(res_l, 'LEFT')
            print_classification(res_r, 'RIGHT')
            
    except Exception as e:
        print(f"Error: {e}")

    finally:
        if (runner):
            runner.stop()