import gdal, os, numpy as np, sys, scipy.ndimage as nd, gc

def CalculateDistribution(arr, mask=None, weight=1):
    #Mascara
    if mask == None:
        maskarr = np.ma.masked_values(arr, 255)
    else:
        maskarr = np.ma.masked_where(mask, arr)
    
    #Calcular variancia
    var = np.var(maskarr)
    std = var**0.5
    
    #Calcular n de elementos
    n = np.sum(maskarr.mask==False)
    
    #Calcular soma
    sum = np.sum(maskarr)
    
    #Calcular media
    mean = np.mean(maskarr)
    
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

def doit(rastInput, output, ratio, valores={1:254,2:127,3:25}, percent=0.5):
    tif = gdal.Open(rastInput)
    driver = tif.GetDriver()
    xsize = tif.RasterXSize
    ysize = tif.RasterYSize
    xSizeDesloc = (xsize-xsize/ratio*ratio)/2
    ySizeDesloc = (ysize-ysize/ratio*ratio)/2
    geoTransform = list(tif.GetGeoTransform())
    geoTransform[0] += geoTransform[1]*int(xSizeDesloc)
    geoTransform[1] *= ratio
    geoTransform[-3] += geoTransform[-1]*int(ySizeDesloc)
    geoTransform[-1] *= ratio
    geoTransform = tuple(geoTransform)
    projection = tif.GetProjectionRef()
    b = tif.GetRasterBand(1)
    arr = b.ReadAsArray()
    for (k,v) in valores.iteritems():
        arr[arr==k]=v
    arr[arr==0]=255
    arr[arr<25]=0
    shape0 = arr.shape[0]/ratio*ratio
    shape1 = arr.shape[1]/ratio*ratio
    arr = arr[int(ySizeDesloc):shape0+int(ySizeDesloc),int(xSizeDesloc):shape1+int(xSizeDesloc)]
    indices=np.indices((shape0, shape1))/ratio
    shape0,shape1 =shape0/ratio, shape1/ratio
    groups = indices[1]+indices[0]*shape1
    mask=(nd.sum(arr==255, groups, range(shape0*shape1))>((ratio**2)*percent)).reshape(shape0,shape1)
    groups[arr==255] = -1
    result=nd.mean(arr, groups, range(shape0*shape1)).reshape(shape0,shape1)+0.5
    result[mask] = 255
    out = driver.Create(str(output), xsize/ratio, ysize/ratio, 1, gdal.GDT_Byte)
    out.SetGeoTransform(geoTransform)
    out.SetProjection(projection)
    dstBand = out.GetRasterBand(1)
    b = None
    tif = None
    dstBand.SetNoDataValue(255)
    dstBand.WriteArray(result)
    dstBand= None
    out = None
    del tif, out, dstBand, b
    gc.collect()
    return CalculateDistribution(result)
    
curDir = os.getcwd()
prevDir = '\\'.join(curDir.split('\\')[:-1])
recortes = ['recorte_paineiras','recorte_cambui','recorte_centro1', 'brandina', 'recorte_brandina']
ratio = int(sys.argv[1])
valores={1:254,2:127,3:25}
percent=0.9999
for i in range(5):
    nome = recortes[i]    
    input = prevDir+'\\'+nome+'.tif'
    output = nome+str(ratio)+'.tif'
    dir = os.path.dirname(input)+'/'
    print nome+": "+str(doit(input,output,ratio,valores,percent))