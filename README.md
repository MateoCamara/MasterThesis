# MasterThesis

This is part of the code I used to carry out my TFM. 

I used two databases to carry out my study on analyzing the subjective quality of video determined by users in subjective tests using neural networks. I used the LIVE laboratory database, and the database proposed by the VQEG. The latter was in a repository where it was not possible to download all the videos at the same time, so I generated a code ("Downloader" directory) to automate the process. It required the use of JDownloader.

My proposal was to evaluate different architectures based on deep learning and determine in terms of computational cost, error and accuracy the characteristics of each of them. They would then be compared relatively with each other, and compared with classical metrics used in the current state of the art. All of them can be found in the "NeuralNetworks" directory.

The classic subjective quality metrics were obtained by means of software prepared for it, or by means of codes developed by me following the pertinent instructions. It can be found in the "QualityMetrics" folder.

In the folder "utils" it can be found some of the codes I used for general tasks. Usually I have worked directly in the Linux console to carry out repetitive tasks or administrative aspects.

Finally, in the folder "CurveFitting" I got a code with which I fit a curve to the specific predicted values. I tried sigmoid and polynomial functions of different degrees.
