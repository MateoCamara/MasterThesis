function [SI_max, TI_max, SI_avg, TI_avg] = complexity(video_url, filter_size)
%'../../Videos/CANDIDATOS/biplano.mp4'
clc;
%while hasFrame(v)
  %  vidFrame = readFrame(v);
fprintf('Cargando vídeo...');
%v = VideoReader(video_url);
%clc
%vHeight = v.height;
%vWidth = v.width;
%s = struct('cdata',zeros(vHeight,vWidth,3, 'uint8'),...
%    'colormap',[]);
s = yuv2mov(video_url, 1280, 720, '420');

%k = 1;
%fprintf('Leyendo vídeo...');
%while hasFrame(v)
%    s(k).cdata = readFrame(v);
%    k = k+1;
%end
%clc

%% COMPLEJIDAD ESPACIAL

SI_max = 0;
SI_avg = 0;
SI_param_avg = 0;

for i = 1:length(s)
    fprintf('Calculando complejidad espacial en el cuadro %d\n', i);
    fprintf('SI_max = %d\n', SI_max);
    %fprintf('SI_avg = %d', SI_avg);
    
    I_gray=rgb2gray(s(i).cdata);
    [SI_param, HV, HVB] = filter_si_hv_adapt(I_gray, filter_size, floor(filter_size/2)); 
    
    SI_param_std = std(SI_param(:));
    SI_param_avg = SI_param_std+SI_param_avg;
    
    if SI_param_std > SI_max
        SI_max = SI_param_std;
    end
    
    if i == length(s)
        SI_avg = SI_param_avg/length(s);
    end
    
    clc   
    
end

%% COMPLEJIDAD TEMPORAL

TI_max = 0;
TI_avg = 0;
dif_avg = 0;

for j = 1:(length(s)-1)
    fprintf('Calculando complejidad temporal en los cuadros %d y %d\n', j, j+1);
    fprintf('TI_max = %d', TI_max);
    %fprintf('TI_avg = %d', TI_avg);
    
    I_gray_1 = rgb2gray(s(j).cdata);
    I_gray_2 = rgb2gray(s(j+1).cdata);
    
    dif = double(I_gray_1-I_gray_2);
    dif_std = std(dif(:));
    dif_avg = dif_avg+dif_std; 
    
    if dif_std > TI_max
        TI_max = dif_std;
    end
    
    if j == (length(s)-1)
        TI_avg = dif_avg/(length(s)-1);
    end
    
    clc;
    
end

%I = imread(s(30).cdata);
%imshow(I, 'Colormap', summer(256));
%imshow(Ib);
%figure;
%image(Ib);
%currAxes.Visible = 'off';
%pause(1/vidObj.FrameRate);