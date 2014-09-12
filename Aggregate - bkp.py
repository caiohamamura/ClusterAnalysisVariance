import gdal
from optparse import Values
import gdal_calc
import sys
import os
import numpy

def Aggregate(rastInput, output, ratio):
    
    tif = gdal.Open(rastInput, gdal.GA_ReadOnly)
    driver = tif.GetDriver()
    xsize = tif.RasterXSize
    ysize = tif.RasterYSize
    out = driver.Create(str(output), xsize/ratio, ysize/ratio, 1, gdal.GDT_Byte)
    
    srcBand = tif.GetRasterBand(1)
    dstBand = out.GetRasterBand(1)
    
    res = gdal.RegenerateOverview(srcBand, dstBand, "average")
    if (res != 0):
        raise("RegenerateOverview() failed with error %d" % res)
    tif = None
    arr = dstBand.ReadAsArray()
    var = numpy.var(numpy.ma.masked_values(arr, 255))**0.5
    diff=127-abs(127-numpy.mean(numpy.ma.masked_values(arr, 255)))
    return var/(diff)
    

'''Dados de entrada'''
ratio = int(sys.argv[1])
for i in range(4):
    recortes = ['recorte_brandina','recorte_cambui','recorte_centro1','recorte_paineiras']
    nome = recortes[i]
    input = 'C:/Users/Caio/Box Sync/Artigo Lea/'+nome+'.tif'
    arvoreIndice = 2
    output = nome+str(ratio)+'.tif'
    
    dir = os.path.dirname(input)+'/'



    if (os.path.dirname(output) == ''):
        output = dir+output

    '''Dados binarios'''
    sys.argv = ['C:\\OSGeo4W\\bin\\gdal_calc.py', '-A', input, '--calc=254*(A=='+ str(arvoreIndice)+')']
    gdal_calc.doit(Values({'A': input, 'C': None, 'B': None, 'creation_options': [], 'C_band': 0, 'format': 'GTiff', 'B_band': 0, 'allBands': '', 'NoDataValue': None, 'outF': dir+'arvore_binario.tif', 'A_band': 0, 'debug': None, 'calc': '254*(A=='+ str(arvoreIndice)+')', 'type': None, 'overwrite': 1}),[])
    print Aggregate(dir+'arvore_binario.tif',output, ratio)