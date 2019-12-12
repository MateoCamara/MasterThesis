

import subprocess
import os


#./run_vmaf yuv420p 3840 2048 \
#  /media/moc/Data1/u/moc/TFM/QP_TESTS/collection/aux/output/IrishCow_3840x2048/QP_TEST/IrishCow_3840x2048.yuv \
#  /media/moc/Data1/u/moc/TFM/QP_TESTS/collection/aux/output/IrishCow_3840x2048/QP_TEST/vmaf_test/yuv/IrishCow_3840x2048_QP_10_00:00:29.yuv \

#./ffmpeg2vmaf width height reference_path distorted_path [--out-fmt output_format --ci]

'''
NEW VQMT VERSION
https://github.com/lvchigo/VQMT
./vqmt /media/moc/Data/moc/AAVP/test_ts2png/reference_done/Lions_3840x1920_00_00_18_noaudio.yuv 
/media/moc/Alcachofa/moc/METRICS_EXPERIMENT/test/Lions_3840x1920_00_00_18_QP_48.yuv 
3840 1920 230 1 /media/moc/Data/moc/AAVP/pruebita SSIM MSSSIM

'''

def doIt():
        ################################ SOURCE
    dir_orig = '/media/mcl/Maxtor/mcl/LIVE/video_original/'
    #file_orig ='IrishCow_3840x2048.yuv'
    width = '1920'
    height = '1080'


    ############################### TEST
    dir_out = '/home/mcl/metricas_objetivas/'
    dir_test = '/media/mcl/Maxtor/mcl/LIVE/video/'





    for file in os.listdir(dir_orig):
        if file.endswith(".yuv"):
            content = os.path.splitext(file)[0]
            #print(file)


            name = (content.strip().split('_'))[0]# + '_' + (content.strip().split('_'))[1]
            #print(name)
            #print('SOURCE NAME', name)

            for file2 in os.listdir(dir_test):
                if file2.endswith(".yuv"):
                    content2 = os.path.splitext(file2)[0]
                    filenames_txt = dir_out + content2 + '_run_vmqt.sh'
                    name2 = (content2.strip().split('_'))[0] #+ '_' + (content2.strip().split('_'))[1] 
                    #print(name2)                    
                    results_name = (content2.strip().split('_'))[0] + '_' + (content2.strip().split('_'))[1]# + '_' + (content2.strip().split('_'))[2]
                    #print('CODIFIED NAME', (content2.strip().split('_'))[0] + '_' + (content2.strip().split('_'))[1] + '_' + (content2.strip().split('_'))[2])
                    if name == name2:
                        print('trueeeeeeeeeeeee')
                        #os.system('/home/mcl/Desktop/VQMT-master/build/bin/Release/vqmt ' + dir_orig + file + ' ' + dir_test + file2 + ' 1072 1920 250 1 ' + results_name + ' VIFP')#' PSNR SSIM MSSSIM PSNRHVS PSNRHVSM')                      
                        os.system('/home/mcl/Desktop/VQMT-master/build/bin/Release/vqmt ' + dir_orig + file + ' ' + dir_test + file2 + ' 720 1280 250 1 ' + results_name + ' VIFP')#' PSNR SSIM MSSSIM PSNRHVS PSNRHVSM')




doIt();