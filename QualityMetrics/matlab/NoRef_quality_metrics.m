clear all; close all; clc;

addpath('msssim','vif','psnr_hvs','divine','bliinds2','biqi','matlab', ...
    'matlabPyrTools-master', 'libsvm-3.23', 'libsvm-3.23/matlab');

path_original = '/media/mcl/Maxtor/mcl/LIVE/original/';
path_distorted = '/media/mcl/Maxtor/mcl/LIVE/cuadros/';

T = table("video", "psnr", "psnr_hvs", "psnr_hvs_m", "ssim", "msssim", "vif", ...
    "BRISQUE", "BLIINDS", "BIQI");

fid = fopen('./directorios_live.csv');
tline = fgetl(fid);
tline = fgetl(fid);
while ischar(tline)
    
    tline_original = split(tline, '_');
    tline_original = strcat(tline_original{1},'_org');
    
    
    path_original_alv = strcat(path_original,char(tline_original),'/');
    path_distorted_alv = strcat(path_distorted,char(tline),'/');
    
    files_original = dir(path_original_alv);
    files_distorted = dir(path_distorted_alv);
    
    alv = 1;
    alvergaso = 1;
    
    tic
    
    for i=3:440
        
        
        
        if mod(i, 10) == 3

            i_dist = imread(strcat(path_distorted_alv, files_distorted(i).name));
            i_orig = imread(strcat(path_original_alv, files_original(i).name));
            i_dist_g = rgb2gray(i_dist);
            i_orig_g = rgb2gray(i_orig);
            i_dist_g_d = im2double(i_dist_g);
            i_orig_g_d = im2double(i_orig_g);

            PSNR(alv) = psnr(i_dist_g, i_orig_g);
            SSIM(alv) = ssim(i_dist_g, i_orig_g);
            BRISQUE(alv) = brisque(i_dist_g);
            VIF(alv) = vifvec(i_dist_g_d, i_orig_g_d);
            [p_hvs_m(alv), p_hvs(alv)] = psnrhvsm(i_dist_g, i_orig_g);
            MSSSIM(alv) = msssim(i_dist_g, i_orig_g);
            %DIIVINE(alv) = divine(i_dist_g);
            if mod(i,80) == 3
                BLIINDS(alvergaso) = bliinds2_score(i_dist_g);
                alvergaso = alvergaso+1;
            end
            BIQI(alv) = biqi(i_dist_g);
            alv = alv+1;
            
        end
        
    end
    
    alv = 1;
    alvergaso = 1;
    
    toc
    
    psnr_media = mean(PSNR);
    ssim_media = mean(SSIM);
    brisque_media = mean(BRISQUE);
    vif_media = mean(VIF);
    p_hvs_media = mean(p_hvs);
    p_hvs_m_media = mean(p_hvs_m);
    msssim_media = mean(MSSSIM);
    %diivine_media = mean(DIIVINE);
    bliinds_media = mean(BLIINDS);
    biqi_media = mean(BIQI);
    
    % "video", "psnr", "psnr_hvs", "psnr_hvs_m", "ssim", "msssim", "vif", ...
    % "DIIVINE", "BRISQUE", "BLIINDS", "BIQI"
    
    cell_metrics = {tline, psnr_media, p_hvs_media, p_hvs_m_media, ...
        ssim_media, msssim_media, vif_media, brisque_media, ...
        bliinds_media, biqi_media};
    
    T = [T; cell_metrics]
            
    tline = fgetl(fid);
end

