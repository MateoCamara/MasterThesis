function [SI_max, TI_max, SI_avg, TI_avg] = complexity_window(video_url, filter_size, num_of_windows)

if ~exist('num_of_windows','var')
     % third parameter does not exist, so default it to something
     num_of_windows = 10;
end

%'../../Videos/CANDIDATOS/biplano.mp4'
clc;
%while hasFrame(v)
  %  vidFrame = readFrame(v);
fprintf('Cargando vídeo...');
v = VideoReader(video_url);
clc
vHeight = v.height;
vWidth = v.width;
s = struct('cdata',zeros(vHeight,vWidth,3, 'uint8'),...
    'colormap',[]);

k = 1;
fprintf('Leyendo vídeo...');
while hasFrame(v)
    s(k).cdata = readFrame(v);
    k = k+1;
end

window_size = floor(length(s)/num_of_windows);

clc

%% COMPLEJIDAD ESPACIAL

SI_max(num_of_windows) = 0;
SI_avg(num_of_windows) = 0;
SI_param_avg = 0;
j=1;
k=0;

for i = 1:length(s)
    k=k+1;
    if mod(i,window_size) == 0 && j < num_of_windows
        j=j+1;
    end
    
    clc
    
    fprintf('Calculando complejidad espacial en el cuadro %d\n', i);
    fprintf('Calculando complejidad espacial en la ventana %d\n', j);
    fprintf('SI_max = %d\n', SI_max(j));
    %fprintf('SI_avg = %d', SI_avg);
    
    I_gray=rgb2gray(s(i).cdata);
    [SI_param, HV, HVB] = filter_si_hv_adapt(I_gray, filter_size, floor(filter_size/2)); 
    
    SI_param_std = std(SI_param(:));
    SI_param_avg = SI_param_std+SI_param_avg;
    
    if SI_param_std > SI_max(j)
        SI_max(j) = SI_param_std;
    end
    
    if (mod(i+1,window_size) == 0 && j < num_of_windows) || i == length(s)
        SI_avg(j) = SI_param_avg/k;
        SI_param_avg=0;
        k=0;
    end   
    
end

%% COMPLEJIDAD TEMPORAL

TI_max(num_of_windows) = 0;
TI_avg(num_of_windows) = 0;
dif_avg = 0;
j=1;
k=0;

for i = 1:(length(s)-1)
    k=k+1;
    if mod(i,window_size) == 0 && j < num_of_windows
        j=j+1;
    end
    
    clc;
    
    fprintf('Calculando complejidad temporal en los cuadros %d y %d\n', i, i+1);
    fprintf('Calculando complejidad espacial en la ventana %d\n', j);
    fprintf('TI_max = %d\n', TI_max);
    %fprintf('TI_avg = %d', TI_avg);
    
    I_gray_1 = rgb2gray(s(i).cdata);
    I_gray_2 = rgb2gray(s(i+1).cdata);
    
    dif = double(I_gray_1-I_gray_2);
    dif_std = std(dif(:));
    dif_avg = dif_avg+dif_std; 
    
    if dif_std > TI_max(j)
        TI_max(j) = dif_std;
    end
    
    if (mod(i+1,window_size) == 0 && j < num_of_windows) || i == (length(s)-1)
        TI_avg(j) = dif_avg/k;
        dif_avg=0;
        k=0;
    end
    
end

%I = imread(s(30).cdata);
%imshow(I, 'Colormap', summer(256));
%imshow(Ib);
%figure;
%image(Ib);
%currAxes.Visible = 'off';
%pause(1/vidObj.FrameRate);
