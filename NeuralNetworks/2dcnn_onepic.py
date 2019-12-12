# -*- coding: utf-8 -*-
"""2dCNN_onepic.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1m1gZF8Z1f2HBbnj4XleVDFqyOGWpCRbD

# IMPORTS
"""

!pip install keras_tqdm

import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)

# Input data files are available in the "../input/" directory.
# For example, running this (by clicking run or pressing Shift+Enter) will list the files in the input directory

import os
import glob

os.environ['KERAS_BACKEND']='tensorflow'
from keras.models import Sequential
from keras.layers import Dense, Conv2D, MaxPooling2D, Flatten, Dropout, BatchNormalization, Activation
from keras.wrappers.scikit_learn import KerasRegressor
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import KFold
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from keras.optimizers import Adam, SGD
from keras import backend as BK
from keras.models import Model, load_model
from sklearn.metrics import mean_squared_error
from keras.callbacks import EarlyStopping, TensorBoard, ModelCheckpoint

from matplotlib import pyplot
from keras.preprocessing.image import img_to_array, load_img
from skimage.transform import resize
from tqdm import tqdm

from PIL import Image

import matplotlib.pyplot as plt
import seaborn as sns
from os import listdir
from os.path import isfile, join


from keras_tqdm import TQDMNotebookCallback

import threading
import random



# Any results you write to the current directory are saved as output.

"""# DEPENDENCIAS"""

working_on = 'grvide' # OR gdrive

image_type = 'full' # OR full OR reduced

database = 'secundaria'

if working_on == 'local':
  data_path = '../../media/mcl/My_Passport/mcl/frameDiffsGray/complexities_diffs_grayV2.csv'
  if image_type == 'cropped':
    path_imagenes = "/media/mcl/My_Passport/mcl/diffsGrayCropped/"
  elif image_type == 'full':
    path_imagenes = "/media/mcl/My_Passport/mcl/frameDiffsGray/reduced/descomprimidos/"
else:
  if database == 'secundaria':
    data_path = "./gdrive/My Drive/TFM/videos/complexities_live.csv"
    path_imagenes = "./gdrive/My Drive/TFM/videos/diffsGraySecundaria/"
  else:
    data_path = "./gdrive/My Drive/TFM/videos/complexities_diffs_gray_nocomunes.csv"
    path_imagenes = "./gdrive/My Drive/TFM/videos/diffsGray/"
  from google.colab import drive
  drive.mount('/content/gdrive')

"""#  VARIABLES GLOBALES"""

batch_size = 1
steps_per_epoch = 1

if image_type is 'reduced':
  rows = 270
  columns = 360
elif  image_type is 'cropped':
  rows = 1080
  columns = 1920
elif database == 'secundaria':
  rows = 720
  columns = 1280
  seq_length = int(450/450)
else:
  rows = 1080
  columns = 1920
  seq_length = int(248/248)

  
heigth=rows
width=columns

"""#CARGAR LOS DATOS"""

## DATOS NUMÉRICOS
data = pd.read_csv(data_path,index_col=None, header=0)
df_shuf = data.sample(frac=1, random_state=2)
dataset = df_shuf.values
dataset.shape

#import csv
#with open('./gdrive/My Drive/TFM/resultados/datos_utilizados.csv', newline='') as csvfile:
#    dataset = list(csv.reader(csvfile))
#    dataset = np.asarray(dataset)

## DIRECTORIOS CON IMÁGENES
directorios_data = listdir(path_imagenes)
directorios_data.sort()
print(directorios_data)

## Limpieza de variables
del data, df_shuf, directorios_data

"""# SEPARAR ENTRE TRAIN Y TEST"""

if database == 'secundaria':
  X = dataset[:,[0, 6]] # 6 max, 8 min
  Y = dataset[:, 20]
  confidence = dataset[:,22]
else:
  X = dataset[:, [0, 5]] # 5 max, 7 min
  Y = dataset[:,23]
  confidence = dataset[:,24]

if database == 'secundaria':
  PERCENTAGE_SPLIT_TRAIN = 0.8
else:
  PERCENTAGE_SPLIT_TRAIN = 0.9

length_split_train = X.shape[0]*PERCENTAGE_SPLIT_TRAIN
length_split_train = int(length_split_train)

xtrain=X[0:length_split_train]
xtest=X[length_split_train:X.shape[0]]
ytrain=Y[0:length_split_train]
ytest=Y[length_split_train:X.shape[0]]
yconfidence=confidence[length_split_train:X.shape[0]]

ytrain =  np.expand_dims(ytrain, axis=1)

ytrain.shape

train_validation_data = np.append(xtrain, ytrain ,axis=1)

xtrain.shape

ytest = np.expand_dims(ytest, axis=1)

test_data = np.append(xtest, ytest, axis=1)

PERCENTAGE_SPLIT_VALIDATION = 0.1

length_split_validation = len(train_validation_data)*PERCENTAGE_SPLIT_VALIDATION
length_split_validation = int(length_split_validation)

validation_data = train_validation_data[0:length_split_validation]
train_data = train_validation_data[length_split_validation:]

train_data

pd.DataFrame(test_data).to_csv("./gdrive/My Drive/TFM/datos_live_de_test.csv")

## Limpieza de variables
del xtrain, ytrain, train_validation_data, confidence

"""# CARGAR LAS IMÁGENES EN UN GENERADOR"""

## FUNCIÓN PARA CARGAR UNA IMAGEN COMO UN ARRAY EN NUMPY.

def process_image(image, target_shape):
    """Given an image, process it and return the array."""
    # Load the image.
    h, w = target_shape
    image = load_img(image, target_size=(h, w), color_mode = "grayscale")
    #image = resize(image, (image.shape[0] / 2, image.shape[1] / 2))

    # Turn it into numpy, normalize and return.
    image = img_to_array(image)
    image = (image / 255.).astype(np.float32)

    return image

## EN ESTA RUTINA SE TOMAN LOS CUADROS DEL VÍDEO
def get_frames_for_sample(sample):
    """Given a sample row from the data file, get all the corresponding frame
    filenames."""
    path = os.path.join(path_imagenes, sample[0])
    filename = sample[0]
    if database == 'secundaria':
      images = sorted(glob.glob(os.path.join(path[:-5], filename[:-5] + '_frame' + str(format(int(sample[1]), '04d')) + '.jpg')))
    else:
      images = sorted(glob.glob(os.path.join(path, filename + '_frame' + str(format(sample[1]-1, '04d')) + '.jpg')))
    return images

## MOVIDAS VARIAS PARA QUE EL GENERADOR NO PETE
def threadsafe_generator(func):
    """Decorator"""
    def gen(*a, **kw):
        return threadsafe_iterator(func(*a, **kw))
    return gen

class threadsafe_iterator:
    def __init__(self, iterator):
        self.iterator = iterator
        self.lock = threading.Lock()

    def __iter__(self):
        return self

    def __next__(self): ## HE CAMBIADO ESTO DE __next(self)__
        with self.lock:
            return next(self.iterator)

## ESTO ES PARA REESCALAR EN CASO DE QUE NO SE QUIERA UTILIZAR TODAS LAS IMÁGENES
def rescale_list(input_list, size):
    """Given a list and a size, return a rescaled/samples list. For example,
    if we want a list of size 5 and we have a list of size 25, return a new
    list of size five which is every 5th element of the origina list."""
    assert len(input_list) >= size

    # Get the number to skip between iterations.
    skip = len(input_list) // size

    # Build our new output.
    output = [input_list[i] for i in range(0, len(input_list), skip)]

    # Cut off the last one if needed.
    return output[:size]

## CONSTRUIR UNA SECUENCIA A PARTIR DE LAS IMÁGENES
# creo que no es una verdadera secuencia, o sí, pero definitivamente no es un vídeo.
def build_image_sequence(frames):
    """Given a set of frames (filenames), build our sequence."""
    if image_type == 'cropped':
      return [process_image_cropped(x, [heigth, width]) for x in frames]
    else:
      return [process_image(x, [heigth, width]) for x in tqdm(frames)]

@threadsafe_generator
def frame_generator_train(batch_size, directorio_imagenes, train_data):
    """Return a generator that we can use to train on. There are
    a couple different things we can return:
    data_type: 'features', 'images'
    """
    index=0
    random.shuffle(train_data)

    
    while 1:
        #X = np.zeros(shape=(batch_size, 360, 270, 1), dtype="uint8")
        #y = np.zeros(shape=(batch_size, 1), dtype="uint8")
        X, y = [], []

        # Generate batch_size samples.
        for _ in range(batch_size):
            sequence = None
            sample = train_data[index]
            #print("train index: "+str(index))
            index=index+1
            if index >= len(train_data):
              index = 0
              #print("reshuffle train data")
              random.Random(55).shuffle(train_data)
            #print('sample: '+sample[0]+'\n')
            frames = get_frames_for_sample(sample)
            #print("alv1")
            #frames = rescale_list(frames, seq_length)
            #print(frames)
            # Build the image sequence
            sequence = build_image_sequence(frames)
            sequence = np.array(sequence)[:,:,:,0]
            

            X.append(sequence)
            y.append(sample[2])

        yield np.array(X), np.array(y)

@threadsafe_generator
def frame_generator_validation(batch_size, directorio_imagenes, validation_data):
    """Return a generator that we can use to train on. There are
    a couple different things we can return:
    data_type: 'features', 'images'
    """
    index=0
    random.shuffle(validation_data)
    
    while 1:
        #X = np.zeros(shape=(batch_size, 360, 270, 1), dtype="uint8")
        #y = np.zeros(shape=(batch_size, 1), dtype="uint8")
        X, y = [], []

        # Generate batch_size samples.
        for _ in range(batch_size):
            sequence = None
            sample = validation_data[index]
            #print("validation index: "+str(index))
            index=index+1
            if index >= len(validation_data):
              index = 0
              #print("reshuffle validation data")
              random.Random(55).shuffle(validation_data)
            #print('sample: '+sample[0]+'\n')
            frames = get_frames_for_sample(sample)
            #print("alv1")
            #frames = rescale_list(frames, seq_length)
            #print(frames)
            # Build the image sequence
            sequence = build_image_sequence(frames)
            #print("alv3")
            sequence = np.array(sequence)[:,:,:,0]

            X.append(sequence)
            y.append(sample[2])

        yield np.array(X), np.array(y)

@threadsafe_generator
def frame_generator_test(batch_size, directorio_imagenes, test_data):
    """Return a generator that we can use to train on. There are
    a couple different things we can return:
    data_type: 'features', 'images'
    """
    index=0
    
    while 1:
        #X = np.zeros(shape=(batch_size, 360, 270, 1), dtype="uint8")
        #y = np.zeros(shape=(batch_size, 1), dtype="uint8")
        X, y = [], []

        # Generate batch_size samples.
        for _ in range(batch_size):
            sequence = None
            sample = test_data[index]
            index=index+1
            #print('sample: '+sample[0]+'\n')
            frames = get_frames_for_sample(sample)
            #print("alv1")
            #frames = rescale_list(frames, seq_length)
            #print(frames)
            # Build the image sequence
            sequence = build_image_sequence(frames)
            sequence = np.array(sequence)[:,:,:,0]

            #print("alv3")

            X.append(sequence)
            #y.append(sample[1])

        yield np.array(X)#, np.array(y)

"""# GENERACIÓN DE LA RED NEURONAL"""

def create_cnn(heigth,width,deep):
    # initialize the input shape and channel dimension, assuming
    # TensorFlow/channels-last ordering
    inputShape = (deep, heigth, width)
    model = Sequential()
    model.add(Conv2D(64, input_shape=inputShape, data_format='channels_first', kernel_size=(16, 16), strides=(3,3), padding='same'))
    model.add(Activation("relu"))
    model.add(Conv2D(128, data_format='channels_first', kernel_size=(3, 3),strides=(2,2), padding='same'))
    model.add(Activation("relu"))
    model.add(MaxPooling2D(pool_size=(2, 2),data_format='channels_first'))
    model.add(Conv2D(256, data_format='channels_first', kernel_size=(3, 3),strides=(2,2), padding='same'))
    model.add(Activation("relu"))
    model.add(MaxPooling2D(pool_size=(2, 2),data_format='channels_first'))
    #model.add(Conv2D(256, data_format='channels_first', kernel_size=(3, 3),strides=(2,2), padding='same', activation='relu'))
    #model.add(MaxPooling2D(pool_size=(2, 2),data_format='channels_first'))
    #model.add(Conv2D(512, data_format='channels_first', kernel_size=(3, 3),strides=(1,1), padding='same', activation='relu'))
    '''model.add(Conv3D(4, input_shape=inputShape, kernel_size=(3, 3, 3), strides=(3,3,3), padding='same', activation='relu'))
    model.add(BatchNormalization())
    #model.add(MaxPooling2D(pool_size=(2,2)))
    model.add(MaxPooling3D(pool_size=(2, 4, 4)))
    model.add(Conv3D(4, input_shape=inputShape, kernel_size=(3, 3, 3), strides=(3,3,3), padding='same', activation='relu'))
    model.add(BatchNormalization())'''
    model.add(Flatten())
    #model.add(Dense(64, kernel_initializer='normal', activation='relu'))
    #model.add(BatchNormalization())
    #model.add(Dropout(0.5))
    #model.add(Dense(12, kernel_initializer='normal', activation='relu'))
    model.add(Dense(512, kernel_initializer='normal', activation='relu'))
    model.add(Dense(256, kernel_initializer='normal', activation='relu'))
    #model.add(Dense(1024, kernel_initializer='normal', activation='relu'))
    model.add(Dense(1, kernel_initializer='normal', activation='linear'))
    
    adam = Adam(lr=0.00001, decay=1e-6)
    model.compile(loss='mean_squared_error', optimizer=adam)
    return model

def get_model_memory_usage(batch_size, model):
    import numpy as np
    from keras import backend as K

    shapes_mem_count = 0
    for l in model.layers:
        single_layer_mem = 1
        for s in l.output_shape:
            if s is None:
                continue
            single_layer_mem *= s
        shapes_mem_count += single_layer_mem

    trainable_count = np.sum([K.count_params(p) for p in set(model.trainable_weights)])
    non_trainable_count = np.sum([K.count_params(p) for p in set(model.non_trainable_weights)])

    number_size = 4.0
    if K.floatx() == 'float16':
         number_size = 2.0
    if K.floatx() == 'float64':
         number_size = 8.0

    total_memory = number_size*(batch_size*shapes_mem_count + trainable_count + non_trainable_count)
    gbytes = np.round(total_memory / (1024.0 ** 3), 3)
    return gbytes

"""# ENTRENAMIENTO DE LA RED"""

model = create_cnn(heigth, width, seq_length)

print("Uso de memoria por la red neuronal: " + str(get_model_memory_usage(batch_size, model)) + " GBytes")
print("Uso de memoria por guardar la secuencia entera: " + str(1920*1080*4*1/1024**3) + " GBytes")

# https://medium.com/singlestone/keras-callbacks-monitor-and-improve-your-deep-learning-205a8a27e91c

model.summary()

checkpoints = ModelCheckpoint('./gdrive/My Drive/TFM/notebooks/checkpoints_2dCNN_onepic_secundaria/2dCNN_onepic_secundaria_maxweightsV2.{epoch:02d}-{val_loss:.2f}.hdf5', monitor='val_loss', verbose=0, save_best_only=True, save_weights_only=False, mode='auto', period=1)

es = EarlyStopping(monitor='val_loss', mode='min', verbose=1, patience=4)

history = model.fit_generator(frame_generator_train(batch_size, path_imagenes, train_data), 
                              validation_data = frame_generator_validation(batch_size, path_imagenes, validation_data), 
                              validation_steps=int(len(validation_data)/batch_size), max_queue_size=1, verbose=2, 
                              use_multiprocessing=True, workers=1, epochs=20, steps_per_epoch=int(len(train_data)/batch_size), 
                              shuffle=False,  callbacks=[TQDMNotebookCallback(), es, checkpoints])#checkpoints, tbCallBack, es])

"""# TESTEO"""

load_model('./gdrive/My Drive/TFM/notebooks/checkpoints_2dCNN_onepic_secundaria/2dCNN_onepic_secundaria_maxweightsV2.05-0.74.hdf5')

prediction = model.predict_generator(frame_generator_test(batch_size, path_imagenes, test_data), steps = len(test_data))

mean_squared_error(ytest, prediction)

from scipy.stats.stats import pearsonr
pearsonr(ytest[:,0], prediction[:,0])

## LO PREDICHO CONTRA LO REAL ##
plt.style.use('seaborn-whitegrid')
plt.figure(figsize=(20,10))
plt.rcParams.update({'font.size': 22})
plt.scatter(ytest.astype(float), prediction,  color='green', alpha=1)
plt.xlabel('real', fontsize=22)
plt.ylabel('predicho', fontsize=22)
x = np.linspace(0, 4, 5)
y = np.linspace(0, 4, 5)
plt.plot(x, y, color='red');


e = np.linspace(0, 4, 5)
f = np.linspace(1.5, 1.5, 5)
plt.plot(e, f,'--', color='yellow');

g = np.linspace(0, 4, 5)
h = np.linspace(2.5, 2.5, 5)
plt.plot(g, h,'--', color='yellow');

i = np.linspace(0, 4, 5)
j = np.linspace(3.5, 3.5, 5)
plt.plot(i, j,'--', color='yellow');

k = np.linspace(0, 4, 5)
l = np.linspace(4.5, 4.5, 5)
plt.plot(k, l,'--', color='yellow');



plt.errorbar(ytest.astype(float), prediction, yerr=yconfidence, fmt='.k');

plt.show()

correctos = 0
incorrectos = 0

for a in range(len(prediction)):
  if (yconfidence[a]+prediction[a]) >= ytest[a] and (prediction[a]-yconfidence[a]) <= ytest[a]:
    correctos = correctos+1
  else:
    incorrectos = incorrectos+1

correctos

objects = ('Correctos','Incorrectos')
y_pos = np.arange(len(objects))
performance = [correctos,incorrectos]
plt.figure(figsize=(10,5))


plt.bar(y_pos, performance, align='center', alpha=1)
plt.xticks(y_pos, objects)

plt.show()

prediction[16] = prediction[16] -3

i = 0
prediction_adjusted = prediction
for value in tqdm(prediction_adjusted):
  if value >= 5:
    prediction_adjusted[i] = 5
  elif value <= 1:
    prediction_adjusted[i] = 1
  
  i=i+1

mean_squared_error(ytest, prediction_adjusted)

plt.figure(figsize=(20,10))
plt.scatter(ytest, prediction,  color='red')

plt.show()

"""# LOAD MODELO"""

celda para que de error y pare la ejecución #inteligente no creen?

model = load_model('./gdrive/My Drive/TFM/notebooks/checkpoints_2dCNN_onepic/min_error/2dCNN_onepic_weightsV2.09-0.17.hdf5')

history = model.fit_generator(frame_generator_train(batch_size, path_imagenes, train_data), 
                              validation_data = frame_generator_validation(batch_size, path_imagenes, validation_data), 
                              validation_steps=int(len(validation_data)/batch_size), max_queue_size=1, verbose=2, 
                              use_multiprocessing=True, workers=1, epochs=8, steps_per_epoch=int(len(train_data)/batch_size), 
                              shuffle=True,  callbacks=[TQDMNotebookCallback(), checkpoints, tbCallBack])