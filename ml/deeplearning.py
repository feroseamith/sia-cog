import numpy
import keras
import json
import datetime
import os
import csv
import pandas
from pandas import read_csv
from Interface import utility
from keras.models import Sequential, model_from_json
from keras import layers
from keras.wrappers.scikit_learn import KerasRegressor, KerasClassifier
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import KFold
from sklearn import preprocessing
from tinydb import TinyDB, Query

modellist = []

def getLayer(m):
    l = layers.Dense()
    if m['type'] == 'dense':
        l = layers.Dense()
    elif m['type'] == 'conv1d':
        l = layers.Conv1D()
    elif m['type'] == 'conv2d':
        l = layers.Conv2D()
    elif m['type'] == 'conv3d':
        l = layers.Conv3D()
    elif m['type'] == 'maxpool1d':
        l = layers.MaxPooling1D()

    if "activation" in m:
        l.activation = m['activation']

    return l


def buildModel(modelDef, fromFile = False, modelFolder=""):
    if fromFile:
        json_file = open(modelFolder + '/model.out', 'r')
        loaded_model_json = json_file.read()
        json_file.close()
        model = model_from_json(loaded_model_json)
        model.load_weights(modelFolder + "/model.hdf5")
    else:
        model = Sequential()
        for m in modelDef['options']['layers']:
            if m['type'] == 'input':
                model.add(layers.Dense(m['val'], input_dim=m['dim'], kernel_initializer=m['init'], activation=m['activation']))
            elif m['type'] == 'dense':
                model.add(layers.Dense(m['val'], kernel_initializer=m['init'], activation=m['activation']))
            elif m['type'] == 'output':
                model.add(layers.Dense(m['val'], kernel_initializer=m['init']))
    

    model_json = model.to_json()
    return model_json

def Train(model, X, Y, weightpath, epoch=32, batch_size=32, validation_split = None):
    if type(X) is pandas.DataFrame:
        X = X.values

    if type(Y) is pandas.DataFrame:
        Y = Y.values

    seed = 7
    numpy.random.RandomState(seed)
    if validation_split is None:
        hist = model.fit(X, Y, epochs=epoch, batch_size=batch_size, verbose=1)
    else:
        hist = model.fit(X, Y, validation_split=validation_split, epochs=epoch, batch_size=batch_size, verbose=1)

    model.save_weights(weightpath)
    return hist.history

def Predict(modelDef, modelFolder, testFile):
    foundModel = False
    name = modelDef['name']
    for m in modellist:
        if m['name'] == name:
            model = m['model']
            foundModel = True
    if not foundModel:
        model = buildModel(modelDef, fromFile=True, modelFolder=modelFolder)
        modellist.append({"name": name, "model": model})
        utility.updateModelResetCache(name, False)
    else:
        if modelDef['reset_cache']:
            model = buildModel(modelDef, fromFile=True, modelFolder=modelFolder)
            utility.updateModelResetCache(name, False)
            for m in modellist:
                if m['name'] == name:
                    m['model'] = model
                    utility.updateModelResetCache(name, False)
    
    if modelDef['csv']['column_header'] == True:
        dataframe = read_csv(testFile, delim_whitespace=modelDef['csv']['delim_whitespace'])
    else:
        dataframe = read_csv(testFile, delim_whitespace=modelDef['csv']['delim_whitespace'], header=None)
    
    if modelDef['csv']['colsdefined'] == True:
        X_frame = dataframe[modelDef['xcols']]
        Y_frame = dataframe[modelDef['ycols']]
        X = X_frame.values
        Y = Y_frame.values
    else:
        array = dataframe.values
        rsplit = modelDef['csv']['xrange'].split(":")
        X = array[:, int(rsplit[0]):int(rsplit[1])]
        Y = array[:, modelDef['csv']['yrange']]
    
    X = utility.scaleData(modelDef['preprocessdata'], X)
    Y = model.Predict(X.astype('float32'))
    dataframe['Result'] = Y
    dataframe.to_csv(modelFolder + '/dataset/prediction.csv')
    return Y
