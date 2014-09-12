import gdal
from optparse import Values
import gdal_calc
import sys
import os
import numpy

def Aggregate(rastInput, output, ratio, algo = "average"):
    
    tif = gdal.Open(rastInput, gdal.GA_ReadOnly)
    driver = tif.GetDriver()
    xsize = tif.RasterXSize
    ysize = tif.RasterYSize
    geoTransform = list(tif.GetGeoTransform())
    geoTransform[1] *= ratio
    geoTransform[-1] *= ratio
    geoTransform = tuple(geoTransform)
    projection = tif.GetProjectionRef()
    out = driver.Create(str(output), xsize/ratio, ysize/ratio, 1, gdal.GDT_Byte)
    out.SetGeoTransform(geoTransform)
    out.SetProjection(projection)
    srcBand = tif.GetRasterBand(1)
    try:
        dstBand = out.GetRasterBand(1)
    except:
        return -1
    
    res = gdal.RegenerateOverview(srcBand, dstBand, algo)
    if (res != 0):
        raise("RegenerateOverview() failed with error %d" % res)
    tif = None
    srcBand = None
    arr = dstBand.ReadAsArray()
    out = None
    return arr
        
    
def CalculateDistribution(arr, mask=None, weight=1):
    #Mascara
    if mask == None:
        maskarr = numpy.ma.masked_values(arr, 255)
    else:
        maskarr = numpy.ma.masked_where(mask, arr)
    
    #Calcular variancia
    std = numpy.std(maskarr)
    var = std**2
    
    #Calcular n de elementos
    n = numpy.sum(maskarr.mask==False)
    
    #Calcular soma
    sum = numpy.sum(maskarr)
    
    #Calcular media
    mean = numpy.mean(maskarr)
    
    #Calcular numero de 254 que cabem no somatorio e quanto contribuiria esse numero de 254 para a variancia
    n254 = int(sum/254)
    var_n254 = ((254-mean)**2)*n254
    
    #Calcular quanto resta e quanto isso contribuiria para o calculo da variancia
    mod254 = sum % 254
    var_mod254 = (mean-mod254)**2
    
    #Calcular quantos zeros precisaria para atingir a quantidade n e quanto esses zeros contribuiriam para a variancia maxima
    n0 = n-n254-1
    var_zeros = (mean**2)*n0
    
    varmax = (var_n254 + var_mod254 + var_zeros)/n
    stdmax = varmax**0.5
    return 1-(var/varmax)**(1./weight)
    
def BinTransform(input, dictMap, output):
    sys.argv = ['C:\\OSGeo4W\\bin\\gdal_calc.py', '-A', input, '--calc='+"+".join([str(v)+'*(A=='+str(i)+')' for (i,v) in dictMap.iteritems()])+')']
    gdal_calc.doit(Values({'A': input, 'C': None, 'B': None, 'creation_options': [], 'C_band': 0, 'format': 'GTiff', 'B_band': 0, 'allBands': '', 'NoDataValue': 255, 'outF': output, 'A_band': 0, 'debug': None, 'calc': "+".join([str(v)+'*(A=='+str(i)+')' for (i,v) in dictMap.iteritems()]), 'type': None, 'overwrite': 1}),[])
    

'''Dados de entrada'''
curDir = os.getcwd()
prevDir = '\\'.join(curDir.split('\\')[:-1])
ratio = int(sys.argv[1])
recortes = ['recorte_paineiras','recorte_cambui','recorte_centro1','recorte_paineiras', 'brandina', 'recorte_brandina']
arvoreIndice = 1
valorArvore = 254
relvadoIndice = 2
valorRelvado = 150
soloIndice = 3
valorSolo = 0
dict_valores = {arvoreIndice:valorArvore,relvadoIndice:valorRelvado,soloIndice:valorSolo}
noData = 0

for i in range(5):
    nome = recortes[i]    
    input = prevDir+'\\'+nome+'.tif'
    output = nome+str(ratio)+'.tif'
    dir = os.path.dirname(input)+'/'



    if (os.path.dirname(output) == ''):
        output = dir+output

    '''Transformar arvore em 254 e nao arvore em 0'''
    BinTransform(input, dict_valores, dir+'arvore_binario.tif')
    BinTransform(input, {noData: 1}, dir+'mask.tif')
    
    '''Criar mascara onde o valor e 0'''
    mask = Aggregate(dir+'mask.tif', output, ratio, 'mode')
    
    '''Agrupar pixels e calcular medias'''
    medias = Aggregate(dir+'arvore_binario.tif', output, ratio)
    if (type(medias) != type(numpy.array([]))):
        continue
    
    '''Calcular distribuicao'''
    distribution = CalculateDistribution(medias, mask,1)
    print nome+": "+str(distribution)