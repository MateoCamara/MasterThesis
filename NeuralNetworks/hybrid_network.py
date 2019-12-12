# -*- coding: utf-8 -*-
"""superred.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1pEwpcQkyQ2JXKGy2MUkx9xWQoGlOt-h6

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
from keras.layers import Dense, Conv2D, MaxPooling2D, Flatten, Dropout, BatchNormalization, Reshape, Conv3D, MaxPooling3D
from keras.wrappers.scikit_learn import KerasRegressor
from keras.optimizers import Adam
from keras import backend as BK
from keras.models import Model, load_model
from sklearn.metrics import mean_squared_error
from keras.callbacks import EarlyStopping, ModelCheckpoint, Callback

from matplotlib import pyplot
from keras.preprocessing.image import img_to_array, load_img
from tqdm import tqdm_notebook as tqdm

import matplotlib.pyplot as plt
import seaborn as sns
from os import listdir
from os.path import isfile, join


from keras_tqdm import TQDMNotebookCallback

import threading
import random



# Any results you write to the current directory are saved as output.

"""# DEPENDENCIAS"""

working_on = 'local' # OR gdrive

image_type = 'full' # OR full OR reduced

if working_on == 'local':
  data_path = '~/asdf/complexities_diffs_gray_nocomunes.csv'
  if image_type == 'cropped':
    path_imagenes = "/media/mcl/My_Passport/mcl/diffsGrayCropped/"
  elif image_type == 'full':
    path_imagenes_distorted =  "/media/mcl/My_Passport/mcl/frameDiffsGray/reduced/descomprimidos/"
    path_imagenes_original = "/media/mcl/My_Passport/mcl/cuadros_directamente_del_video/"

"""#  VARIABLES GLOBALES"""

seq_length = int(248/5)
batch_size = 1
steps_per_epoch = 1

if image_type is 'reduced':
  rows = 270
  columns = 360
elif  image_type is 'cropped':
  rows = 540
  columns = 960
else:
  rows = 1080
  columns = 1920
  heigth = 1080
  width = 1920

quarter = "quarter0"

"""#CARGAR LOS DATOS"""

## DATOS NUMÉRICOS
data = pd.read_csv(data_path,index_col=None, header=0)
df_shuf = data.sample(frac=1, random_state=1)
dataset = df_shuf.values
dataset.shape

## DIRECTORIOS CON IMÁGENES
directorios_data = listdir(path_imagenes_distorted)
directorios_data.sort()
print(directorios_data)

## Limpieza de variables
del data, df_shuf, directorios_data

"""# SEPARAR ENTRE TRAIN Y TEST"""

X = dataset[:,0]
Y = dataset[:,23]
objective_values = dataset[:,1:23]
confidence = dataset[:,24]

from sklearn import preprocessing

min_max_scaler = preprocessing.MinMaxScaler()
objective_values = min_max_scaler.fit_transform(objective_values)

PERCENTAGE_SPLIT_TRAIN = 0.9

length_split_train = X.shape[0]*PERCENTAGE_SPLIT_TRAIN
length_split_train = int(length_split_train)

xtrain=X[0:length_split_train]
xtest=X[length_split_train:X.shape[0]]
xtrain_objective = objective_values[0:length_split_train]
xtest_objective = objective_values[length_split_train:X.shape[0]]
ytrain=Y[0:length_split_train]
ytest=Y[length_split_train:X.shape[0]]
yconfidence=confidence[length_split_train:X.shape[0]]

xtrain.shape

train_data = np.c_[xtrain, xtrain_objective, ytrain]
train_data = train_data.tolist()

test_data = np.c_[xtest, xtest_objective, ytest]
test_data = test_data.tolist()

train_data[0][23]

## Limpieza de variables
del xtrain, ytrain

"""# CARGAR LAS IMÁGENES EN UN GENERADOR"""

## FUNCIÓN PARA CARGAR UNA IMAGEN COMO UN ARRAY EN NUMPY.

def process_image(image, target_shape):
    """Given an image, process it and return the array."""
    # Load the image.
    h, w = target_shape
    image = load_img(image, target_size=(h, w), color_mode = "grayscale")

    # Turn it into numpy, normalize and return.
    image = img_to_array(image)
    image = (image / 255.).astype(np.float32)

    return image

## EN ESTA RUTINA SE TOMAN LOS CUADROS DEL VÍDEO
def get_frames_for_sample(sample):
    """Given a sample row from the data file, get all the corresponding frame
    filenames."""
    
    """HE CAMBIADO QUE SAMPLE ERA SAMPLE[0]"""
    path = os.path.join(path_imagenes, sample)
    filename = sample#[0]
    images = sorted(glob.glob(os.path.join(path, filename + '*jpg')))
    return images

## EN ESTA RUTINA SE TOMAN LOS CUADROS DEL VÍDEO
def get_frames_for_sample_distorted(sample):
    """Given a sample row from the data file, get all the corresponding frame
    filenames."""
    
    """HE CAMBIADO QUE SAMPLE ERA SAMPLE[0]"""
    path = os.path.join(path_imagenes_distorted, sample)
    filename = sample#[0]
    images = sorted(glob.glob(os.path.join(path, filename + '*jpg')))
    return images

## EN ESTA RUTINA SE TOMAN LOS CUADROS DEL VÍDEO
def get_frames_for_sample_original(sample):
    """Given a sample row from the data file, get all the corresponding frame
    filenames."""
    
    """HE CAMBIADO QUE SAMPLE ERA SAMPLE[0]"""
    path = os.path.join(path_imagenes_original, sample)
    filename = sample#[0]
    images = sorted(glob.glob(os.path.join(path, filename + '*jpg')))
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
      return [process_image(x, [heigth, width]) for x in frames]

@threadsafe_generator
def frame_generator_train(batch_size, directorio_imagenes, train_data):
    """Return a generator that we can use to train on. There are
    a couple different things we can return:
    data_type: 'features', 'images'
    """
    index=0
    image_id=0

    
    while 1:
        #X = np.zeros(shape=(batch_size, 360, 270, 1), dtype="uint8")
        #y = np.zeros(shape=(batch_size, 1), dtype="uint8")
        frame_processed, y = [], []

        # Generate batch_size samples.

        sequence = None
        sample = train_data[index]
        #print("train index: "+str(index))
        index=index+1
        if index >= len(train_data)*248:
          index = 0
          print("reshuffle train data")
          random.shuffle(train_data)
        print('sample: '+str(sample[0])+'\n')
        frames = get_frames_for_sample(sample)
        print("todos los cuadros: "+str(frames))
        frame = frames[image_id]
        print("cuadro utilizado: " + str(frame) + " que cuadra con el id: " + str(image_id))
        image_id = image_id + 1
        if image_id > 248:
          image_id = 0
            
        frame_processed= [process_image_cropped(frame, [rows, columns])]
              
        y = sample[1]
        print("Salida train: "+ str(y))
        
        yield np.array(frame_processed), np.array(y)

@threadsafe_generator
def frame_generator_validation(batch_size, directorio_imagenes, validation_data):
    """Return a generator that we can use to train on. There are
    a couple different things we can return:
    data_type: 'features', 'images'
    """
    index=0
    
    while 1:
        #X = np.zeros(shape=(batch_size, 360, 270, 1), dtype="uint8")
        #y = np.zeros(shape=(batch_size, 1), dtype="uint8")
        frame_processed, y = [], []

        # Generate batch_size samples.
        sequence = None
        sample = validation_data[index]
        #print("validation index: "+str(index))
        index=index+1
        if index >= len(validation_data):
          index = 0
          #print("reshuffle validation data")
          random.shuffle(validation_data)
        print('sample validation: '+str(sample[0])+'\n')
        frames = get_frames_for_sample_cropped(sample)
        print("todos los cuadros validation: "+str(frames))
        frame = frames[image_id]
        print("cuadro utilizado validation: " + str(frame) + " que cuadra con el id: " + str(image_id))
        image_id = image_id + 1
        if image_id > 248:
          image_id = 0
        
        frame_processed= [process_image_cropped(frame, [rows, columns])]
        y = sample[1]
        print("Salida validation: "+ str(y))
            
        yield np.array(frame_processed), np.array(y)

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
            frames = get_frames_for_sample_cropped(sample)
            #print("alv1")
            frames = rescale_list(frames, seq_length)
            #print(frames)
            # Build the image sequence
            sequence = build_image_sequence(frames)
            #print("alv3")

            X.append(sequence)
            #y.append(sample[1])

        yield np.array(X)#, np.array(y)

"""# GENERACIÓN DE LA RED NEURONAL"""

from keras.layers import ConvLSTM2D, MaxPooling2D, Input, Dense, Flatten, Concatenate, Add
from keras.models import Model

def modelo(rows, columns, deep):
  
  #distorted_img = Input(shape=(deep, rows, columns, 1), name='input_original', batch_shape=(1,deep,rows, columns, 1))  ## branch 1 with image input
  #x = Conv3D(64, kernel_size=(16, 16, 5), strides=(1,5,5), padding='same', activation='relu')(distorted_img)
  #x = Conv3D(128, kernel_size=(7, 7, 5), strides=(1,2,2), padding='same', activation='relu')(x)
  #x = MaxPooling3D((2,2,2))(x)
  #x = Conv3D(256, kernel_size=(3, 3, 3), strides=(1,2,2), padding='same', activation='relu')(x)
  #x = MaxPooling3D(pool_size=(2,2,2))(x)
  #x = Flatten()(x)
  #x = Dense(256, kernel_initializer='normal', activation='relu')(x)
  #out_a = Dense(128, activation='relu')(x)

  diff_img = Input(shape=(deep,rows, columns, 1), name='input_diff', batch_shape=[1,deep,rows, columns, 1])        ## branch 2 with numerical input
  x1 = Conv3D(64, kernel_size=(16, 16, 5), strides=(1,5,5), padding='same', activation='relu')(diff_img) #155
  x1 = Conv3D(128, kernel_size=(7, 7, 5), strides=(1,2,2), padding='same', activation='relu')(x1) # 122
  x1 = MaxPooling3D((2,2,2))(x1)
  x1 = Conv3D(256, kernel_size=(3, 3, 3), strides=(1,2,2), padding='same', activation='relu')(x1)
  x1 = MaxPooling3D(pool_size=(2,2,2))(x1)
  x1 = Flatten()(x1)
  x1 = Dense(256, kernel_initializer='normal', activation='relu')(x1)
  x1 = Dense(128, kernel_initializer='normal', activation='relu')(x1)
  out_b = Dense(8, activation='relu')(x1)
  
  objective_value = Input(shape=([len(objective_values[0])]), batch_shape=[1, len(objective_values[0])])
  x2 = Dense(64, activation='relu')(objective_value)
  out_c = Dense(32, activation='relu')(x2)

  #concatenated_images = Concatenate()([out_a, out_b])    ## concatenate the two branches
  #common_images = Dense(128, activation='relu')(concatenated_images)
  #concatenated_images = Dense(64, activation='relu')(concatenated_images)
  #out_images = Dense(32, activation='relu')(concatenated_images)
  concatenated2 = Concatenate()([out_b, out_c])
  
  out = Dense(1, activation='linear')(concatenated2)

  model = Model([diff_img, objective_value], out) # model = Model([distorted_img, diff_img, objective_value], out)
  print(model.summary())
  adam = Adam(lr=1e-6, decay=1e-6)
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

seq_length = 49
model = modelo(rows, columns, seq_length)

print("Uso de memoria: " + str(get_model_memory_usage(batch_size, model)) + " GBytes")

# https://medium.com/singles/keras-callbacks-monitor-and-improve-your-deep-learning-205a8a27e91c

from keras.utils import plot_model
alv = plot_model(model, "alv.png")
plt.show(alv)

## NO SE PUEDE USAR TENSORBOARD CON DATOS DE VALIDACION QUE SEAN GENERADORES
#tbCallBack = TensorBoard(log_dir='./Graph3dCNN', histogram_freq=1, write_graph=True, write_images=True)

#history = model.fit_generator(frame_generator_train(batch_size, path_imagenes, train_data),
 #                             validation_data = frame_generator_validation(batch_size, path_imagenes, validation_data), 
  #                            validation_steps=int(len(validation_data)/batch_size), max_queue_size=1, verbose=2, 
   #                           use_multiprocessing=True, workers=1, epochs=20, steps_per_epoch=int(len(train_data)/batch_size), 
   #                           shuffle=False, callbacks=[TQDMNotebookCallback(), checkpoints, es])

"""# LOCURA"""

#for i in tqdm(range(int(len(test_data)))):
 # sample = test_data[i][0]
  #chequear_frame =  get_frames_for_sample_original(sample)
  #if len(chequear_frame) != 250:
   # print("fallo en: " + sample)
    #assert False

model = load_model('./checkpoints_superred/checkpoint_superred_epoch10_val1.6223512.h5')

#alv = -1
#for j in tqdm(range(len(chequear_frame))):
 # alv += 1
  #for k in range(len(chequear_frame)):
   # if chequear_frame[j] == chequear_frame[k]:
    #  print(chequear_frame[j] + "k=" + str(alv))

from IPython.display import display, clear_output
print('Train...')
for epoch in tqdm(range(20)):
    mean_tr_loss = []
    mean_te_loss = []
    for i in tqdm(range(int(len(train_data)))): #len(train_data)
        y_true = train_data[i][23]
        sample = train_data[i][0]
        objective = train_data[i][1:23]
        #print(np.array(objective_values[i]).reshape(-1, 1))
        
        #print('sample: '+str(sample)+'\n')
        frames_distorted = get_frames_for_sample_distorted(sample)
        ##frames_original = get_frames_for_sample_original(sample)
        #print("todos los cuadros distorted: "+str(frames_distorted))
        #print("todos los cuadros original: "+str(frames_original))        
        frames_distorted = rescale_list(frames_distorted, seq_length)
        ##frames_original = rescale_list(frames_original, seq_length)
        #print("todos los cuadros distorted: "+str(frames_distorted))
        #print("todos los cuadros original: "+str(frames_original))

        sequence_distorted = build_image_sequence(frames_distorted)
        ##sequence_original = build_image_sequence(frames_original)
        #print("cuadro utilizado distorted: " + str(frame_distorted) + " que cuadra con el id: " + str(image_id))
        #print("cuadro utilizado original: " + str(frame_original) + " que cuadra con el id: " + str(image_id))

        #print("alv1")
        X = [np.expand_dims(np.array(sequence_distorted),axis=0),
                np.expand_dims(objective, axis=0)]
        #print(X)
        tr_loss = model.train_on_batch(X, np.array([y_true]))
        #mean_tr_acc.append(tr_acc)
        mean_tr_loss.append(tr_loss)
        print('\r', "Error en la secuencia "+ sample +": " + str(tr_loss), end='')

        #if i == 200 or i == 300:
         # model.save('./gdrive/My Drive/TFM/notebooks/checkpoints_LSTM_truncated/modelo_vuelta'+i+'.h5')

    print('\n loss training = {}'.format(np.mean(mean_tr_loss)))
    #print('___________________________________')
    
    
    ## TEST

    for i in range(int(len(test_data))):
        y_true = test_data[i][23]
        sample = test_data[i][0]
        objective = test_data[i][1:23]

        #print('sample: '+str(sample)+'\n')
        frames_distorted = get_frames_for_sample_distorted(sample)
        #frames_original = get_frames_for_sample_original(sample)
        frames_distorted = rescale_list(frames_distorted, seq_length)
        #print("todos los cuadros: "+str(frames))
        #frame_distorted = frames_distorted[image_id]
        sequence_distorted = build_image_sequence(frames_distorted)    
        #frame_original = frames_original[image_id]
        #print("cuadro utilizado: " + str(frame) + " que cuadra con el id: " + str(image_id))

        #frame_processed_distorted = [process_image(frame_distorted, [rows, columns])]
        #frame_processed_original = [process_image(frame_original, [rows, columns])]

        Z = [np.expand_dims(np.array(sequence_distorted),axis=0),
                    np.expand_dims(objective, axis=0)]

        te_loss = model.test_on_batch(Z, np.array([y_true]))
        #mean_tr_acc.append(tr_acc)
        #print('\r', "Error en la secuencia "+ sample +": " + str(te_loss), end='')

        mean_te_loss.append(te_loss)

    print('loss testing = {}'.format(np.mean(mean_te_loss)))
    print('___________________________________')

    
    model.save('./checkpoints_superred/checkpoint_superred_epoch'+ str(epoch)+'_val'+str(np.mean(mean_te_loss))+'.h5')

## TEST
prediction_global = np.zeros(int(len(test_data)))
for i in tqdm(range(int(len(test_data)))):
    y_true = test_data[i][23]
    sample = test_data[i][0]
    objective = test_data[i][1:23]

    #print('sample: '+str(sample)+'\n')
    frames_distorted = get_frames_for_sample_distorted(sample)
    #frames_original = get_frames_for_sample_original(sample)
    frames_distorted = rescale_list(frames_distorted, seq_length)
    #print("todos los cuadros: "+str(frames))
    #frame_distorted = frames_distorted[image_id]
    sequence_distorted = build_image_sequence(frames_distorted)    
    #frame_original = frames_original[image_id]
    #print("cuadro utilizado: " + str(frame) + " que cuadra con el id: " + str(image_id))

    #frame_processed_distorted = [process_image(frame_distorted, [rows, columns])]
    #frame_processed_original = [process_image(frame_original, [rows, columns])]

    Z = [np.expand_dims(np.array(sequence_distorted),axis=0),
                np.expand_dims(objective, axis=0)]

    prediccion = model.predict_on_batch(Z)#, np.array([y_true]))
    #mean_tr_acc.append(tr_acc)
    #print('\r', "Predicción para el minibatch " + str(image_id) + " en la secuencia "+ sample +": " + str(prediction), end='')

    prediction_global[i] = prediccion#np.mean(mean_prediction)
    print("\npredicción: " + str(prediction_global[i]) + ", real: " + str(y_true))

mean_squared_error(ytest, prediction_global)

alv = ytest.astype(float)

alv2 = np.expand_dims(alv, 1)

from scipy.stats.stats import pearsonr
pearsonr(alv2, prediction_global)

## LO PREDICHO CONTRA LO REAL ##
plt.style.use('seaborn-whitegrid')
plt.figure(figsize=(20,9))
plt.rcParams.update({'font.size': 22})
plt.scatter(ytest.astype(float), prediction_global,  color='green', alpha=1)
plt.xlabel('real', fontsize=22)
plt.ylabel('predicho', fontsize=22)
x = np.linspace(1, 5, 5)
y = np.linspace(1, 5, 5)
plt.plot(x, y, color='red');


e = np.linspace(1, 5, 5)
f = np.linspace(1.5, 1.5, 5)
plt.plot(e, f,'--', color='yellow');

g = np.linspace(1, 5, 5)
h = np.linspace(2.5, 2.5, 5)
plt.plot(g, h,'--', color='yellow');

i = np.linspace(1, 5, 5)
j = np.linspace(3.5, 3.5, 5)
plt.plot(i, j,'--', color='yellow');

k = np.linspace(1, 5, 5)
l = np.linspace(4.5, 4.5, 5)
plt.plot(k, l,'--', color='yellow');



plt.errorbar(ytest.astype(float), prediction_global, yerr=yconfidence, fmt='.k');

plt.show()

actual_prediction = 0
prediction = np.zeros(len(train_data))
for i in tqdm(range(int(len(train_data)))):
  y_true = train_data[i][1]
  sample = train_data[i][0]
  for image_id in np.linspace(1,25,1):#tqdm(range(248)):
    #print('sample: '+str(sample)+'\n')
    image_id = int(image_id)
    frames_distorted = get_frames_for_sample_distorted(sample)
    frames_original = get_frames_for_sample_original(sample)      #print("todos los cuadros: "+str(frames))
    frame_distorted = frames_distorted[image_id]
    frame_original = frames_original[image_id]  #print("cuadro utilizado: " + str(frame) + " que cuadra con el id: " + str(image_id))

    frame_processed_distorted = [process_image(frame_distorted, [rows, columns])]
    frame_processed_original = [process_image(frame_original, [rows, columns])]


    Ø = [np.expand_dims(np.array(frame_processed_distorted),axis=0), np.expand_dims(np.array(frame_processed_original),axis=0),
          np.expand_dims(objective_values[i], axis=0)]

    actual_prediction += model.predict_on_batch(Ø)

    #mean_tr_acc.append(tr_acc)
  
  prediction[i] = actual_prediction/4
  actual_prediction = 0


print("predicción: " + str(prediction) + ", real: " + str(test_data))

print("predicción: " + str(prediction) + ", real: " + str(ytest))

mean_squared_error(ytest, prediction)

from scipy.stats.stats import pearsonr
pearsonr(ytest, prediction)

## LO PREDICHO CONTRA LO REAL ##
plt.figure(figsize=(20,10))
plt.scatter(ytest.astype(float), prediction,  color='green', alpha=1)
plt.xlabel('real')
plt.ylabel('predicho')
plt.title('real contra predicho')
x = np.linspace(1, 5, 5)
y = np.linspace(1, 5, 5)
plt.plot(x, y, color='red');

a = np.linspace(1, 5, 5)
b = np.linspace(1.3, 5.3, 5)
plt.plot(a, b,'--', color='blue');

c = np.linspace(1, 5, 5)
d = np.linspace(0.7, 4.7, 5)
plt.plot(c, d,'--', color='blue');

e = np.linspace(1, 5, 5)
f = np.linspace(1.5, 1.5, 5)
plt.plot(e, f,'--', color='yellow');

g = np.linspace(1, 5, 5)
h = np.linspace(2.5, 2.5, 5)
plt.plot(g, h,'--', color='yellow');

i = np.linspace(1, 5, 5)
j = np.linspace(3.5, 3.5, 5)
plt.plot(i, j,'--', color='yellow');

k = np.linspace(1, 5, 5)
l = np.linspace(4.5, 4.5, 5)
plt.plot(k, l,'--', color='yellow');

plt.show()

'''
    mean_te_acc = []
    mean_te_loss = []
    for i in range(len(X_test)):
        for j in range(max_len):
            te_loss, te_acc = model.test_on_batch(np.expand_dims(np.expand_dims(X_test[i][j], axis=1), axis=1),
                                                  y_test[i])
            mean_te_acc.append(te_acc)
            mean_te_loss.append(te_loss)
        model.reset_states()

        for j in range(max_len):
            y_pred = model.predict_on_batch(np.expand_dims(np.expand_dims(X_test[i][j], axis=1), axis=1))
        model.reset_states()

    print('accuracy testing = {}'.format(np.mean(mean_te_acc)))
    print('loss testing = {}'.format(np.mean(mean_te_loss)))
    print('___________________________________')



              #X = np.zeros(shape=(batch_size, 360, 270, 1), dtype="uint8")
        #y = np.zeros(shape=(batch_size, 1), dtype="uint8")
        frame_processed, y = [], []

        # Generate batch_size samples.

        sequence = None
        sample = train_data[index]
        #print("train index: "+str(index))
        index=index+1
        if index >= len(train_data)*248:
          index = 0
          print("reshuffle train data")
          random.shuffle(train_data)
        print('sample: '+str(sample[0])+'\n')
        frames = get_frames_for_sample(sample)
        print("todos los cuadros: "+str(frames))
        frame = frames[image_id]
        print("cuadro utilizado: " + str(frame) + " que cuadra con el id: " + str(image_id))
        image_id = image_id + 1
        if image_id > 248:
          image_id = 0
            
        frame_processed= [process_image(frame, [rows, columns])]
              
        y = sample[1]
        print("Salida train: "+ str(y))
        
        yield np.array(frame_processed), np.array(y)
        '''

"""# TESTEO"""

prediction = model.predict_generator(frame_generator_test(batch_size, path_imagenes, test_data), steps = len(test_data))

mean_squared_error(ytest, prediction)

pyplot.figure(figsize=(20,10))
pyplot.plot(history.history['loss'], label='train')
pyplot.plot(history.history['val_loss'], label='test')
pyplot.legend()
pyplot.show()

plt.figure(figsize=(20,10))
plt.scatter(ytest, prediction,  color='red')

plt.show()

print(prediction[22])
print(ytest[22])

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