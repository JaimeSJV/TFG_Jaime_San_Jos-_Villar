import cv2
import numpy as np
from django.core.files.uploadedfile import InMemoryUploadedFile

def t_corr(img_file, sol):
    print("Corrigiendo...")
    image_array = np.asarray(bytearray(img_file.read()), dtype=np.uint8)
    img = cv2.imdecode(image_array, cv2.IMREAD_GRAYSCALE)
    img = fix_cuad(img)
    if id_cuad(img) == False:
        print("Cuadricula no valida")
        return 0, 0, 0, "Cuadricula no valida"
    else:
        test = respuestas(img)
        cor, inc, nota, test = corrector(test, sol)
        print("Corregido!")
        return cor, inc, nota, test
    
def pre_AT(i):
    blur = cv2.medianBlur(i, 9)
    edges = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,\
            cv2.THRESH_BINARY_INV, 11, 2)
    
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    edges = cv2.dilate(edges, kernel, iterations= 1)
    edges = cv2.erode(edges, kernel, iterations= 1)
    
    return edges

def pre_O(i):
    blur = cv2.GaussianBlur(i,(5,5),0)
    thresh, edges = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    edges = cv2.dilate(edges, kernel, iterations= 1)
    edges = cv2.erode(edges, kernel, iterations= 1)

    return edges

def contours(e):
    contours, hierarchy = cv2.findContours(e, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
    return contours

def ratio(i, cont):
    mask = np.zeros(i.shape, dtype=np.uint8)
    cv2.drawContours(mask, [cont], -1, (255,255,255), -1)

    cv2.imwrite("1-Contorno_Cuad.jpg", mask)

    x, y, w, h = cv2.boundingRect(cont)
    edges_zoom = mask[y:y+h, x:x+w]

    #h, w = edges_zoom.shape[:2]
    edges_zoom = 255 - edges_zoom
    total_white = cv2.countNonZero(edges_zoom[0:w, 0:h])
    ratio = total_white / float(w*h)
    
    return ratio, h, w, x, y

def max_cont(contours):
    cont = contours[0]
    maxar = cv2.contourArea(cont)
    for c in contours:
        ar = cv2.contourArea(c)
        if ar > maxar:
            maxar = ar
            cont = c
    
    return cont

def esquinas(cont):
    minX = cont[0]
    minY = cont[0]
    MaxX = minX
    MaxY = minY
    for o in cont:
        if o[0][0] < minX[0][0]:
            minX = o
        if o[0][0] > MaxX[0][0]:
            MaxX = o
        if o[0][1] < minY[0][1]:
            minY = o
        if o[0][1] > MaxY[0][1]:
            MaxY = o

    return minX, minY, MaxX, MaxY

def fix_cuad(img):
    edg = pre_O(img)
    #edg = pre_AT(img)
    cv2.imwrite("0-Thresh_Pre.jpg", edg)
    cont = contours(edg)
    m_cont = max_cont(cont)
    return ajuste_img(img, edg, m_cont)

def ajuste_img(i, e, m_cont):
    r, ch, cw, cx, cy = ratio(i, m_cont)

    #Ratio funcional en 0.015
    print("Ratio: " + str(r))
    if r < 0.03:
        x, y, w, h = cv2.boundingRect(m_cont)
        if ch > cw:
            SI = [x, y]
            SD = [x+w, y]
            II = [x, y+h]
            ID = [x+w, y+h]
        else:
            inc = int(ch/8)
            rota_zoom = e[cy-inc:cy+ch+inc, cx-inc:cx+cw+inc]
            ccontours, hierarchy = cv2.findContours(rota_zoom, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            cm_cont = max_cont(ccontours)
            minX = ccontours[0][0]
            minY = ccontours[0][0]
            MaxX = minX
            MaxY = minY
            for i in ccontours:
                for o in i:
                    if o[0][0] < minX[0][0]:
                        minX = o
                    if o[0][0] > MaxX[0][0]:
                        MaxX = o
                    if o[0][1] < minY[0][1]:
                        minY = o
                    if o[0][1] > MaxY[0][1]:
                        MaxY = o
            cx, cy, cw, ch = cv2.boundingRect(cm_cont)
            if  minY[0][1] < cy:
                SI = [x+w, y]
                SD = [x+w, y+h]
                II = [x, y]
                ID = [x, y+h]
            else:
                SI = [x, y+h]
                SD = [x, y]
                II = [x+w, y+h]
                ID = [x+w, y]
 
    else:
        minX, minY, MaxX, MaxY = esquinas(m_cont)
        #Añadir cuadricula no legible
        if minX[0][1] < MaxX[0][1]:
            SI = minX[0]
            SD = minY[0]
            II = MaxY[0]
            ID = MaxX[0]
        else:    
            SI = minY[0]
            SD = MaxX[0]
            II = minX[0]
            ID = MaxY[0]
        
    testing = True

    src = np.float32([SI, SD,
                      II, ID])
    h, w = i.shape[:2]
    dst = np.float32([(10, 10), (w-15, 10),
                      (10, h-10), (w-15, h-10)])
    M = cv2.getPerspectiveTransform(src, dst)
    fix_c = cv2.warpPerspective(e, M, (w, h), flags=cv2.INTER_LINEAR)

    cv2.imwrite("2-Fix_Cuad.jpg", fix_c)
    
    return fix_c

def respuestas(i):
    h_t, w_t = i.shape[:2]
    test = [0 for col in range(60)]
    h_c = int(h_t/15) + 1
    w_c = int(w_t/4) + 1
    zoom_y = int(h_t/45)
    zoom_x = int(w_t/12)
    x = 0
    y = 0
    idz = 0
    while idz < 60:
        celda = i[y+zoom_y:y+h_c-zoom_y, x+zoom_x:x+w_c-zoom_x]
        #if idz < 4:
        #    cv2.imwrite("celda" + str(idz) + ".jpg", celda)
        total_white = cv2.countNonZero(celda)
        r = total_white / float(zoom_x*zoom_y)
        if idz < 4:
            print(r)
        if r > 0.27:
            test[idz] = 1
        idz += 1
        x += w_c
        if x > w_t:
            x = 0
            y += h_c
    idz = 0
    test_l ={}
    row = 0
    while idz < 60:
        num_r = 0
        if test[idz] == 1:
            test_l[row] = 'A'
            num_r += 1
        if test[idz+1] == 1:
            test_l[row] = 'B'
            num_r += 1
        if test[idz+2] == 1:
            test_l[row] = 'C'
            num_r += 1
        if test[idz+3] == 1:
            test_l[row] = 'D'
            num_r += 1
        if num_r != 1:
            test_l[row] = '0'
        idz += 4
        row += 1
    return test_l

def corrector(test, sol):
    nota = 0
    a = 0
    cor = 0
    inc = 0
    sol_l = {}
    for c in sol:
        sol_l[a] = c
        a += 1
    a = 0
    #print(test)
    while a < 15:
        if test[a]!='0':
            if test[a] == sol_l[a]:
                nota += 1
                cor += 1
            else:
                nota -= 0.25
                inc += 1
        a += 1
    test_s = " "
    for a in test:
        test_s = test_s + test[a] + " "
    test_s = test_s.strip()

    nota = (nota/15)*10
    
    return cor, inc, nota, test_s

def cuenta_lin(img, x_min, y_min):
    contours, hierarchy = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    cont = 0
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        new_img = img[y:y+h, x:x+w]
        h, w = new_img.shape[:2]
        if h > y_min and w > x_min:
            cont += 1
    return cont

def id_cuad(fix_cuad):
    kernel_length = np.array(fix_cuad).shape[1]//80
    kernel_length2 = np.array(fix_cuad).shape[1]//50

    y_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, kernel_length))
    x_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_length2, 1))
    
    y_img = cv2.erode(fix_cuad, y_kernel, iterations=3)
    y_lines = cv2.dilate(y_img, y_kernel, iterations=4)
    cv2.imwrite("3-Lineas_Y.jpg", y_lines)  

    x_img = cv2.erode(fix_cuad, x_kernel, iterations=3)
    x_lines = cv2.dilate(x_img, x_kernel, iterations=4)
    cv2.imwrite("4-Lineas_X.jpg", x_lines)

    h, w = fix_cuad.shape[:2]
    y_min = h - (h/4)
    x_min = w - (w/2)
    
    col = cuenta_lin(y_lines, 0, y_min) - 1
    fil = cuenta_lin(x_lines, x_min, 0) - 1
    print("La cuadricula tiene " + str(col) + " columnas y " + str(fil) + " filas")

    if col == 4 and fil == 15:
        return True
    else:
        return False
